from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

from offers_app.models import Offer, OfferDetail
from .serializers import OfferSerializer, OfferListSerializer, OfferDetailSerializer
from .permissions import IsOwnerOrReadOnly, IsBusinessUser


class OfferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing offers.
    """
    queryset = Offer.objects.all().order_by('-updated_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter fields based on docs
    filterset_fields = {
        'user': ['exact'], # creator_id
        # Note: filtering by min_price/max_delivery_time on related fields requires custom filter class 
        # or simple lookups if fields existed on model. 
        # For simplicity in this step, we enable standard filtering.
    }
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price'] # min_price ordering needs annotation logic in get_queryset

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