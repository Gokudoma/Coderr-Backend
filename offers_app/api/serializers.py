from django.db.models import Min
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from offers_app.models import Offer, OfferDetail, Order, Review
from user_auth_app.api.serializers import RegistrationSerializer


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for OfferDetail.
    """
    url = serializers.HyperlinkedIdentityField(view_name='offerdetail-detail')

    class Meta:
        model = OfferDetail
        fields = ['id', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type', 'url']


class OfferListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing offers.
    Includes simplified details (links) and calculated fields.
    """
    details = OfferDetailSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField() 

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at', 
            'updated_at', 'details', 'min_price', 'min_delivery_time', 'user_details'
        ]

    def get_min_price(self, obj):
        min_price = obj.details.aggregate(Min('price'))['price__min']
        return min_price if min_price is not None else 0

    def get_min_delivery_time(self, obj):
        min_time = obj.details.aggregate(Min('delivery_time_in_days'))['delivery_time_in_days__min']
        return min_time if min_time is not None else 0

    def get_user_details(self, obj):
        return {
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "username": obj.user.username
        }


class OfferSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, updating, and retrieving single offers.
    Handles nested write operations for OfferDetails.
    """
    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at', 'details']
        read_only_fields = ['user', 'created_at', 'updated_at']

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


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Reviews.
    """
    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating', 'description', 'created_at', 'updated_at']
        read_only_fields = ['reviewer', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['reviewer'] = self.context['request'].user
        if Review.objects.filter(business_user=validated_data['business_user'], reviewer=validated_data['reviewer']).exists():
            raise ValidationError("You have already reviewed this user.")
        return super().create(validated_data)


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Orders.
    Handles the creation logic by copying OfferDetail data.
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