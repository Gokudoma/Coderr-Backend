from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OfferViewSet, OfferDetailViewSet, OrderViewSet, ReviewViewSet,
    BaseInfoView, OrderCountView, CompletedOrderCountView
)

router = DefaultRouter()
router.register(r'offers', OfferViewSet, basename='offer')
router.register(r'offerdetails', OfferDetailViewSet, basename='offerdetail')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('base-info/', BaseInfoView.as_view(), name='base-info'),
    path('order-count/<int:pk>/', OrderCountView.as_view(), name='order-count'),
    path('completed-order-count/<int:pk>/', CompletedOrderCountView.as_view(), name='completed-order-count'),
    path('', include(router.urls)),
]