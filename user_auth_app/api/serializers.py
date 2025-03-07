from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from ..models import Profile

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True, required=True)
    user_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = User
        fields = ('user_id', 'username', 'email', 'password', 'repeated_password')  # Ohne 'type'

    def validate(self, data):
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({"password": "Passwörter stimmen nicht überein."})
        return data

    def create(self, validated_data):
        validated_data.pop('repeated_password')  # Entferne das wiederholte Passwort
        user = User.objects.create_user(**validated_data)  # Erstelle den User
        return user

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True) 

    class Meta:
        model = Profile
        fields = ['user', 'username', 'first_name', 'last_name', 'email', 'file', 
                  'location', 'tel', 'description', 'working_hours', 'type', 'created_at']

