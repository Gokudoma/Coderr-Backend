from django.contrib.auth import authenticate, get_user_model
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
        if data.get('password') != data.get('repeated_password'):
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        validated_data.pop('repeated_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            type=validated_data['type']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Validates email and password credentials.
    """
    username = serializers.CharField() # We use email as username, but field is mostly named username in DRF
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, data):
        email = data.get('username')
        password = data.get('password')

        if email and password:
            # We treat the input 'username' as email for authentication
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            if not user:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Must include 'username' (email) and 'password'.")

        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing and updating user profiles.
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'type',
            'file', 'location', 'tel', 'description', 'working_hours', 
            'date_joined'
        ]
        read_only_fields = ['id', 'email', 'type', 'date_joined', 'username']