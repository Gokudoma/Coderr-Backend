from django.db import models
from django.db.models import Min, Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import Offer, OfferDetail, Order, Review
from user_auth_app.models import CustomUser
from .filters import OfferFilter, ReviewFilter
from .pagination import OfferPagination
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
    pagination_class = OfferPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = OfferFilter
    
    # We allow ordering by calculated fields and standard fields
    ordering_fields = ['min_price', 'updated_at']
    search_fields = ['title', 'description']

    def get_queryset(self):
        """
        Annotate queryset with min_price and min_delivery_time.
        This is crucial for the filters to work without throwing 500 errors.
        """
        return Offer.objects.annotate(
            min_price=Min('details__price'),
            min_delivery_time=Min('details__delivery_time_in_days')
        ).order_by('-updated_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return OfferListSerializer
        return OfferSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        if self.action == 'retrieve':
            return [IsAuthenticated()]
        if self.action == 'create':
            return [IsAuthenticated(), IsBusinessUser()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OfferDetailViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing specific offer details directly.
    """
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders.
    Restricts visibility to order participants, but allows Staff/Admins to see all.
    """
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
            
        if user.is_authenticated:
            return Order.objects.filter(
                models.Q(customer_user=user) | models.Q(business_user=user)
            )
        return Order.objects.none()

    def get_permissions(self):
        """
        Permissions based on requirements:
        - Create: Customer only
        - Update: Business Owner only (status updates)
        - Delete: Admin/Staff only
        - List/Retrieve: Participants only
        """
        if self.action == 'create':
            return [IsAuthenticated(), IsCustomer()] 
        if self.action == 'destroy':
            return [IsAuthenticated(), IsAdminUser()]
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsOrderBusinessOwner()] 
        return [IsAuthenticated(), IsOrderParticipant()]


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ReviewFilter
    ordering_fields = ['updated_at', 'rating']

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsCustomer()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticatedOrReadOnly()]


class BaseInfoView(APIView):
    """
    Returns platform-wide statistics.
    Public access.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        review_count = Review.objects.count()
        average_rating = Review.objects.aggregate(Avg('rating'))['rating__avg'] or 0
        business_profile_count = CustomUser.objects.filter(type='business').count()
        offer_count = Offer.objects.count()

        return Response({
            "review_count": review_count,
            "average_rating": round(average_rating, 1),
            "business_profile_count": business_profile_count,
            "offer_count": offer_count
        })


class OrderCountView(APIView):
    """
    Returns count of 'in_progress' orders for a specific business user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        get_object_or_404(CustomUser, pk=pk)
        count = Order.objects.filter(business_user_id=pk, status='in_progress').count()
        return Response({"order_count": count})


class CompletedOrderCountView(APIView):
    """
    Returns count of 'completed' orders for a specific business user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        get_object_or_404(CustomUser, pk=pk)
        count = Order.objects.filter(business_user_id=pk, status='completed').count()
        return Response({"completed_order_count": count})