from rest_framework import status, generics, permissions
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .serializers import RegistrationSerializer, LoginSerializer, UserProfileSerializer

User = get_user_model()


class RegistrationView(APIView):
    """
    API endpoint for user registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'username': user.username,
                'email': user.email,
                'user_id': user.pk
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(ObtainAuthToken):
    """
    API endpoint for user login.
    Returns auth token and user details.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'username': user.username,
            'email': user.email,
            'user_id': user.pk
        })


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to retrieve and update user profiles.
    Users can only update their own profile.
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Custom logic could be added here if needed, 
        # standard IsAuthenticated protects the endpoint generally.
        # Object level permission to only allow owner to edit is handled below or via custom permission class.
        return super().get_permissions()

    def update(self, request, *args, **kwargs):
        # Ensure user can only update their own profile
        instance = self.get_object()
        if instance != request.user:
            return Response(
                {"detail": "You do not have permission to edit this profile."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)


class BusinessProfileListView(generics.ListAPIView):
    """
    API endpoint to list all business profiles.
    """
    queryset = User.objects.filter(type='business')
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny] # Or IsAuthenticated depending on requirements


class CustomerProfileListView(generics.ListAPIView):
    """
    API endpoint to list all customer profiles.
    """
    queryset = User.objects.filter(type='customer')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated] # Usually restricted