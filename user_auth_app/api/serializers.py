from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Handles password confirmation and user creation.
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    repeated_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'type']

    def validate(self, data):
        """
        Check that both passwords match.
        """
        if data.get('password') != data.get('repeated_password'):
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        """
        Create a new user with encrypted password.
        """
        # Remove repeated_password before creating user
        validated_data.pop('repeated_password')
        
        # Create user using create_user helper (handles hashing)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            type=validated_data['type']
        )
        return user