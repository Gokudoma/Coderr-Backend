from django.db.models import Min, Q, Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAdminUser
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from user_auth_app.models import CustomUser

from offers_app.models import Offer, OfferDetail, Order, Review
from .permissions import (
    IsBusinessUser, IsOwnerOrReadOnly, IsCustomer,
    IsOrderParticipant, IsOrderBusinessOwner
)
from .serializers import (
    OfferDetailSerializer, OfferListSerializer, OfferSerializer,
    OrderSerializer, ReviewSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 100


class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.annotate(
        min_price_annotated=Min('details__price')
    ).order_by('-updated_at')
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter
    ]
    search_fields = ['title', 'description']
    ordering_fields = ['min_price', 'updated_at']

    def get_queryset(self):
        qs = super().get_queryset()
        creator_id = self.request.query_params.get('creator_id')
        if creator_id:
            qs = qs.filter(user_id=creator_id)

        min_price = self.request.query_params.get('min_price')
        if min_price:
            qs = qs.filter(details__price__gte=min_price).distinct()

        max_delivery = self.request.query_params.get('max_delivery_time')
        if max_delivery:
            qs = qs.filter(
                details__delivery_time_in_days__lte=max_delivery
            ).distinct()
        return qs

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return OfferListSerializer
        return OfferSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        if self.action == 'retrieve':
            return [IsAuthenticated()]
        if self.action == 'create':
            return [IsBusinessUser()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OfferDetailViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        # Allow admins to see all orders so they can delete them
        if user.is_staff:
            return Order.objects.all()
        
        # Regular users only see their own orders
        if user.is_authenticated:
            return Order.objects.filter(
                Q(customer_user=user) | Q(business_user=user)
            )
        return Order.objects.none()

    def get_permissions(self):
        if self.action == 'create':
            return [IsCustomer()]
        if self.action in ['update', 'partial_update']:
            return [IsOrderBusinessOwner()]
        if self.action == 'destroy':
            return [IsAdminUser()]
        return [IsOrderParticipant()]


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['business_user', 'reviewer']
    ordering_fields = ['updated_at', 'rating']

    def get_permissions(self):
        if self.action == 'create':
            return [IsCustomer()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


class BaseInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        review_count = Review.objects.count()
        avg_rating = Review.objects.aggregate(Avg('rating'))['rating__avg']
        avg_rating = round(avg_rating, 1) if avg_rating else 0.0
        business_count = CustomUser.objects.filter(type='business').count()
        offer_count = Offer.objects.count()

        return Response({
            "review_count": review_count,
            "average_rating": avg_rating,
            "business_profile_count": business_count,
            "offer_count": offer_count
        })


class OrderCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        count = Order.objects.filter(
            business_user_id=pk,
            status='in_progress'
        ).count()
        return Response({"order_count": count})


class CompletedOrderCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        count = Order.objects.filter(
            business_user_id=pk,
            status='completed'
        ).count()
        return Response({"completed_order_count": count})