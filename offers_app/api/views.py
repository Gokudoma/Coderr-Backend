from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from offers_app.models import Offer, OfferDetail, Order, Review
from .permissions import (
    IsBusinessUser, IsCustomer, IsOrderBusinessOwner, IsOrderParticipant,
    IsOwnerOrReadOnly
)
from .serializers import (
    OfferDetailSerializer, OfferListSerializer, OfferSerializer,
    OrderSerializer, ReviewSerializer
)


class OfferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing offers.
    Supports filtering, searching, and ordering.
    """
    queryset = Offer.objects.all().order_by('-updated_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'user': ['exact'], 
    }
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']

    def get_serializer_class(self):
        if self.action == 'list':
            return OfferListSerializer
        return OfferSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsBusinessUser()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        return [IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OfferDetailViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing specific offer details directly.
    """
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders.
    Restricts visibility to order participants.
    """
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Order.objects.filter(
                models.Q(customer_user=user) | models.Q(business_user=user)
            )
        return Order.objects.none()

    def get_permissions(self):
        if self.action == 'create':
            return [IsCustomer()] 
        if self.action in ['update', 'partial_update']:
            return [IsOrderBusinessOwner()] 
        return [IsOrderParticipant()]


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsCustomer()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        return [IsAuthenticatedOrReadOnly()]