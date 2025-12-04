from rest_framework import serializers
from django.db.models import Min
from offers_app.models import Offer, OfferDetail
from user_auth_app.api.serializers import RegistrationSerializer # Or a specific UserSerializer if you have one


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
    # We assume you might want a simplified user object here
    user_details = serializers.SerializerMethodField() 

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at', 
            'updated_at', 'details', 'min_price', 'min_delivery_time', 'user_details'
        ]

    def get_min_price(self, obj):
        # Calculates the minimum price from related details
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
        """
        Create Offer and nested OfferDetails.
        """
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(**validated_data)
        
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        
        return offer

    def update(self, instance, validated_data):
        """
        Update Offer and handle nested OfferDetails.
        Strategy: Update fields on Offer, replace Details (or update if logic requires).
        For simplicity and typical PUT/PATCH behavior on nested lists: 
        We often clear and recreate or update specifically. 
        Here we update offer fields.
        """
        details_data = validated_data.pop('details', None)
        
        # Update Offer fields
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.image = validated_data.get('image', instance.image)
        instance.save()

        # Handle details update if provided
        if details_data is not None:
            # Simple strategy: Delete old, create new. 
            # (Note: In production, you might want to update existing IDs to preserve them)
            instance.details.all().delete()
            for detail_data in details_data:
                OfferDetail.objects.create(offer=instance, **detail_data)

        return instance