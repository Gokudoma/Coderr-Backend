from django.db.models import Min
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from offers_app.models import Offer, OfferDetail, Order, Review


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for the OfferDetail endpoint and nested write operations.
    Includes validation to ensure 400 Bad Request on invalid input.
    """
    # Adding basic validation to trigger 400 errors on bad input
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    delivery_time_in_days = serializers.IntegerField(min_value=1)

    class Meta:
        model = OfferDetail
        fields = [
            'id', 'title', 'revisions', 'delivery_time_in_days',
            'price', 'features', 'offer_type'
        ]


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """
    Serializer for listing OfferDetails as simple links within an Offer.
    """
    url = serializers.HyperlinkedIdentityField(
        view_name='offerdetail-detail',
        read_only=True
    )

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']


class BaseOfferSerializer(serializers.ModelSerializer):
    """
    Base Serializer containing shared calculated fields.
    """
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    def get_min_price(self, obj):
        if hasattr(obj, 'min_price'):
            return obj.min_price if obj.min_price is not None else 0
        val = obj.details.aggregate(Min('price'))['price__min']
        return val if val is not None else 0

    def get_min_delivery_time(self, obj):
        if hasattr(obj, 'min_delivery_time'):
            return obj.min_delivery_time if obj.min_delivery_time is not None else 0
        val = obj.details.aggregate(Min('delivery_time_in_days'))['delivery_time_in_days__min']
        return val if val is not None else 0


class OfferListSerializer(BaseOfferSerializer):
    """
    Serializer for GET /api/offers/
    """
    details = OfferDetailLinkSerializer(many=True, read_only=True)
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at',
            'updated_at', 'details', 'min_price', 'min_delivery_time',
            'user_details'
        ]

    def get_user_details(self, obj):
        return {
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "username": obj.user.username
        }


class OfferRetrieveSerializer(BaseOfferSerializer):
    """
    Serializer for GET /api/offers/{pk}/
    """
    details = OfferDetailLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at',
            'updated_at', 'details', 'min_price', 'min_delivery_time'
        ]


class OfferWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating (POST) and updating (PATCH) offers.
    Returns full nested details in the response.
    """
    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'image', 'description', 'details'
        ]

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(**validated_data)
        
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        
        return offer

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)
        
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.image = validated_data.get('image', instance.image)
        instance.save()

        if details_data is not None:
            instance.details.all().delete()
            for detail_data in details_data:
                OfferDetail.objects.create(offer=instance, **detail_data)

        return instance

    def to_representation(self, instance):
        """
        Manually construct the response to match the documentation requirements.
        """
        data = super().to_representation(instance)
        data['id'] = instance.id
        data['details'] = OfferDetailSerializer(instance.details.all(), many=True).data
        return data


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Reviews.
    """
    class Meta:
        model = Review
        fields = [
            'id', 'business_user', 'reviewer', 'rating', 
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reviewer', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['reviewer'] = self.context['request'].user
        exists = Review.objects.filter(
            business_user=validated_data['business_user'],
            reviewer=validated_data['reviewer']
        ).exists()
        if exists:
            raise ValidationError("You have already reviewed this user.")
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.pop('business_user', None)
        return super().update(instance, validated_data)


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Orders.
    """
    offer_detail_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'customer_user', 'business_user', 'title', 'revisions', 
            'delivery_time_in_days', 'price', 'features', 'offer_type', 
            'status', 'created_at', 'updated_at', 'offer_detail_id'
        ]
        read_only_fields = [
            'customer_user', 'business_user', 'title', 'revisions', 
            'delivery_time_in_days', 'price', 'features', 'offer_type', 
            'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        offer_detail_id = validated_data.pop('offer_detail_id')
        
        try:
            offer_detail = OfferDetail.objects.get(pk=offer_detail_id)
        except OfferDetail.DoesNotExist:
            raise ValidationError({"offer_detail_id": "Invalid ID."})

        order = Order.objects.create(
            customer_user=self.context['request'].user,
            business_user=offer_detail.offer.user,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
            status='in_progress',
            **validated_data
        )
        return order