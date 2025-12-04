from django.urls import path
from .views import (
    RegistrationView, 
    CustomLoginView, 
    UserProfileDetailView,
    BusinessProfileListView,
    CustomerProfileListView
)

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', CustomLoginView.as_view(), name='login'),
    
    # Profile Endpoints
    path('profile/<int:pk>/', UserProfileDetailView.as_view(), name='profile-detail'),
    path('profiles/business/', BusinessProfileListView.as_view(), name='profile-business-list'),
    path('profiles/customer/', CustomerProfileListView.as_view(), name='profile-customer-list'),
]