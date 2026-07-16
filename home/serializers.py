from rest_framework import serializers
from .models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'device_id', ]



class FaceVerificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['verification_face']



class ReturnCustomUserSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(use_url=True, required=False)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    department = serializers.CharField(required=False)
    matric_number = serializers.CharField(required=False)
    level = serializers.CharField(required=False)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'matric_number', 'department', 'level', 'profile_image' ]



class ReturnLecturerSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    department = serializers.CharField(required=False)
    minimum_attendance = serializers.IntegerField(required=False)
    token_expiration_time = serializers.IntegerField(required=False)
    profile_image = serializers.ImageField(use_url=True, required=False)
    token_refresh_time = serializers.IntegerField(required=False)

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'department', 'profile_image', 'minimum_attendance', 'token_expiration_time', 'token_refresh_time']