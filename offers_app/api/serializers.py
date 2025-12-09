from django.db.models import Min
from rest_framework import serializers
from offers_app.models import Offer, OfferDetail, Order, Review


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for full OfferDetail representation.
    Used in POST/PATCH responses and /offerdetails/{id}/.
    """
    class Meta:
        model = OfferDetail
        fields = [
            'id', 'title', 'revisions', 'delivery_time_in_days',
            'price', 'features', 'offer_type'
        ]


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """
    Serializer for OfferDetail links.
    Used in GET /offers/ and GET /offers/{id}/.
    """
    url = serializers.HyperlinkedIdentityField(
        view_name='offerdetail-detail',
        read_only=True
    )

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']


class OfferListSerializer(serializers.ModelSerializer):
    """
    Serializer for GET requests (List & Retrieve).
    Shows details as links.
    Matches documentation:
    - Includes: user, created_at, updated_at, min_price
    - Excludes: user_details
    """
    user = serializers.IntegerField(source='user.id', read_only=True)
    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at',
            'updated_at', 'details', 'min_price', 'min_delivery_time'
        ]

    def get_min_price(self, obj):
        if hasattr(obj, 'min_price_annotated'):
            return obj.min_price_annotated or 0
        val = obj.details.aggregate(Min('price'))['price__min']
        return val if val is not None else 0

    def get_min_delivery_time(self, obj):
        val = obj.details.aggregate(
            Min('delivery_time_in_days')
        )['delivery_time_in_days__min']
        return val if val is not None else 0


class OfferSerializer(serializers.ModelSerializer):
    """
    Serializer for POST/PATCH.
    Matches documentation (clean response):
    - Includes: id, title, image, description, details
    - Excludes: user, created_at, updated_at
    """
    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'image', 'description', 'details'
        ]
        # user, created_at, updated_at are intentionally removed from fields

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(**validated_data)
        
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)

        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get(
            'description', instance.description
        )
        instance.image = validated_data.get('image', instance.image)
        instance.save()

        if details_data is not None:
            for detail_data in details_data:
                offer_type = detail_data.get('offer_type')
                if offer_type:
                    existing_detail = instance.details.filter(
                        offer_type=offer_type
                    ).first()

                    if existing_detail:
                        existing_detail.title = detail_data.get(
                            'title', existing_detail.title
                        )
                        existing_detail.revisions = detail_data.get(
                            'revisions', existing_detail.revisions
                        )
                        existing_detail.delivery_time_in_days = detail_data.get(
                            'delivery_time_in_days',
                            existing_detail.delivery_time_in_days
                        )
                        existing_detail.price = detail_data.get(
                            'price', existing_detail.price
                        )
                        existing_detail.features = detail_data.get(
                            'features', existing_detail.features
                        )
                        existing_detail.save()
                    else:
                        OfferDetail.objects.create(
                            offer=instance, **detail_data
                        )
        return instance


class OrderSerializer(serializers.ModelSerializer):
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
            detail = OfferDetail.objects.get(pk=offer_detail_id)
        except OfferDetail.DoesNotExist:
            msg = "Invalid ID."
            raise serializers.ValidationError({"offer_detail_id": msg})

        return Order.objects.create(
            customer_user=self.context['request'].user,
            business_user=detail.offer.user,
            title=detail.title,
            revisions=detail.revisions,
            delivery_time_in_days=detail.delivery_time_in_days,
            price=detail.price,
            features=detail.features,
            offer_type=detail.offer_type,
            status='in_progress'
        )


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'id', 'business_user', 'reviewer', 'rating', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['reviewer', 'created_at', 'updated_at']

    def validate(self, data):
        request = self.context.get('request')
        if request and request.method == 'POST':
            existing = Review.objects.filter(
                business_user=data.get('business_user'),
                reviewer=request.user
            ).exists()
            if existing:
                msg = "You have already reviewed this user."
                raise serializers.ValidationError(msg)
        return data