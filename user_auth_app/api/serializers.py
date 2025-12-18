from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Handles password confirmation and user creation.
    """
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
            raise serializers.ValidationError({"password": "Passwords must match."})
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
    """
    Serializer for user login.
    Validates username and password credentials.
    """
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user_obj = User.objects.filter(username=username).first()
            
            if user_obj:
                user = authenticate(
                    request=self.context.get('request'),
                    username=user_obj.email,
                    password=password
                )
            else:
                user = None

            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials."
                )
        else:
            raise serializers.ValidationError(
                "Must include 'username' and 'password'."
            )

        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing and updating user profiles.
    Used for the detailed profile view.
    """
    user = serializers.IntegerField(source='id', read_only=True)
    created_at = serializers.DateTimeField(
        source='date_joined',
        read_only=True,
        format='%Y-%m-%dT%H:%M:%SZ'
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
        read_only_fields = ['user', 'username', 'type', 'created_at']

    def to_representation(self, instance):
        """
        Ensures that null values for specific fields are returned as empty strings.
        """
        data = super().to_representation(instance)
        fields_to_check = [
            'first_name', 'last_name', 'location', 'tel',
            'description', 'working_hours', 'file'
        ]
        for field in fields_to_check:
            if data.get(field) is None:
                data[field] = ""
        return data


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for the Business Profile List.
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
        """
        Ensures that null values are returned as empty strings.
        """
        data = super().to_representation(instance)
        fields_to_check = [
            'first_name', 'last_name', 'location', 'tel',
            'description', 'working_hours', 'file'
        ]
        for field in fields_to_check:
            if data.get(field) is None:
                data[field] = ""
        return data


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for the Customer Profile List.
    Matches the documentation JSON structure (reduced fields).
    """
    user = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = User
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'type'
        ]
        read_only_fields = ['user', 'type', 'username']

    def to_representation(self, instance):
        """
        Ensures that null values are returned as empty strings.
        """
        data = super().to_representation(instance)
        fields_to_check = ['first_name', 'last_name', 'file']
        for field in fields_to_check:
            if data.get(field) is None:
                data[field] = ""
        return data