from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Movie, Review
from datetime import date


# Custom Validators
def validate_positive_duration(value):
    #Duration must be positive number
    if value <= 0:
        raise serializers.ValidationError("Duration must be greater than 0 minutes")
    return value


def validate_delivery_mode(value):
    #Delivery mode must be THEATER or STREAMING
    allowed_modes = ['THEATER', 'STREAMING']
    if value.upper() not in allowed_modes:
        raise serializers.ValidationError(f"Delivery mode must be either THEATER or STREAMING")
    return value.upper()


def validate_name_not_blank(value):
    #Name cannot be empty or whitespace only
    if not value or value.strip() == '':
        raise serializers.ValidationError("Movie name cannot be blank")
    return value


def validate_release_date_not_future(value):
    #Release date cannot be in the future
    if value > date.today():
        raise serializers.ValidationError("Release date cannot be in the future")
    return value


# Movie Serializer
class MovieSerializer(serializers.ModelSerializer):
    # Apply custom validators to fields
    name = serializers.CharField(max_length=200, validators=[validate_name_not_blank])
    duration = serializers.IntegerField(validators=[validate_positive_duration])
    delivery_mode = serializers.CharField(max_length=20, validators=[validate_delivery_mode])
    release_date = serializers.DateField(validators=[validate_release_date_not_future])

    class Meta:
        model = Movie
        fields = ['id', 'name', 'description', 'actor', 'duration', 'delivery_mode', 'keywords', 'release_date']
        # id is read-only by default


# User Serializer for registration in API
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)
    password2 = serializers.CharField(write_only=True, min_length=4, label="Confirm Password")

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'password2', 'email']
        extra_kwargs = {
            'email': {'required': False},
        }

    def validate(self, data):
        # Check if passwords match
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match"})
        return data

    def create(self, validated_data):
        # Remove password2 before creating user
        validated_data.pop('password2')
        # Create user with hashed password
        user = User.objects.create_user(**validated_data)
        return user


# Review Serializer
class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    movie_name = serializers.CharField(source='movie.name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'username', 'movie', 'movie_name', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'username', 'movie_name', 'created_at', 'updated_at']

    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate_comment(self, value):
        """Validate comment is not empty"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Comment cannot be blank")
        return value
