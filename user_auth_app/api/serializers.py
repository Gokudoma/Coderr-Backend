from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    repeated_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'type']

    def validate(self, data):
        if data.get('password') != data.get('repeated_password'):
            raise serializers.ValidationError(
                {"password": "Passwords must match."}
            )
        return data

    def create(self, validated_data):
        validated_data.pop('repeated_password')
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            type=validated_data['type']
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            if not user:
                msg = "Unable to log in with provided credentials."
                raise serializers.ValidationError(msg)
        else:
            msg = "Must include 'username' and 'password'."
            raise serializers.ValidationError(msg)

        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the detailed profile view (Owner perspective).
    Includes email and created_at.
    """
    user = serializers.IntegerField(source='id', read_only=True)
    created_at = serializers.DateTimeField(
        source='date_joined',
        read_only=True,
        format="%Y-%m-%dT%H:%M:%S%z"
    )
    location = serializers.CharField(required=False, allow_blank=True)
    tel = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    working_hours = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'location', 'tel', 'description', 'working_hours',
            'type', 'email', 'created_at'
        ]
        read_only_fields = [
            'user', 'email', 'type', 'created_at', 'username'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        fields = [
            'first_name', 'last_name', 'location', 'tel',
            'description', 'working_hours', 'file'
        ]
        for field in fields:
            if data.get(field) is None:
                data[field] = ""
        return data


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for the Business Profile List.
    Matches the documentation JSON structure (includes location, tel, etc.).
    Excludes email and created_at.
    """
    user = serializers.IntegerField(source='id', read_only=True)
    location = serializers.CharField(required=False, allow_blank=True)
    tel = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    working_hours = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'location', 'tel', 'description', 'working_hours',
            'type'
        ]
        read_only_fields = ['user', 'type', 'username']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure null fields are empty strings
        fields = [
            'first_name', 'last_name', 'location', 'tel',
            'description', 'working_hours', 'file'
        ]
        for field in fields:
            if data.get(field) is None:
                data[field] = ""
        return data


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for the Customer Profile List.
    Matches the documentation JSON structure:
    - Includes 'uploaded_at' (mapped from date_joined).
    - Excludes location, tel, description, working_hours.
    """
    user = serializers.IntegerField(source='id', read_only=True)
    uploaded_at = serializers.DateTimeField(
        source='date_joined',
        read_only=True,
        # Format matching ISO-like string in docs
        format="%Y-%m-%dT%H:%M:%S"
    )

    class Meta:
        model = User
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'uploaded_at', 'type'
        ]
        read_only_fields = ['user', 'type', 'username', 'uploaded_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure null fields are empty strings
        # Only check fields present in this serializer
        fields = ['first_name', 'last_name', 'file']
        for field in fields:
            if data.get(field) is None:
                data[field] = ""
        return data