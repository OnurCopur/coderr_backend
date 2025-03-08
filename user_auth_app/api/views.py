from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import RegistrationSerializer

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from django.contrib.auth import authenticate
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404
from ..models import Profile
from .serializers import ProfileSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication


User = get_user_model()

class RegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # Erstelle den User mit den Validierungsdaten
        response = super().create(request, *args, **kwargs)

        # Hole den User aus der Response
        user = User.objects.get(username=response.data['username'])

        # Hole den 'type' aus den Request-Daten
        type_value = request.data.get('type')

        # Erstelle automatisch ein Profil für den Benutzer und speichere den 'type' im Profil
        Profile.objects.create(user=user, email=user.email, type=type_value)

        # Token für den User erstellen
        token, created = Token.objects.get_or_create(user=user)

        # Füge das Token zu den Antwortdaten hinzu
        response.data['token'] = token.key

        # Entferne das Passwort aus der Antwort
        if 'password' in response.data:
            del response.data['password']

        return Response(response.data)



class CustomLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        # Gast-Login Logik (Überprüfung der Gast-Benutzernamen)
        if username in ['guest_customer', 'guest_business'] and password == 'guest':
            # Gast-Benutzer erstellen, falls er noch nicht existiert
            user, created = User.objects.get_or_create(
                username=username
            )

            # Erstelle ein Dummy-Token für den Gast-Benutzer
            token, _ = Token.objects.get_or_create(user=user)

            # Erfolgreiche Antwort mit Token und Benutzer-Details
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'role': 'guest'  # Hier eine spezielle Rolle für Gast-Benutzer
            }, status=status.HTTP_200_OK)

        # Normale Benutzer-Authentifizierung
        user = authenticate(username=username, password=password)

        if user:
            # Token für den normalen Benutzer erstellen oder holen
            token, _ = Token.objects.get_or_create(user=user)

            # Erfolgreiche Antwort mit Token und Benutzer-Details
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,  # E-Mail bleibt für normale Benutzer
                'role': getattr(user, 'role', 'user')  # Normale Benutzer erhalten ihre Rolle
            }, status=status.HTTP_200_OK)

        # Fehlerfall, wenn die Anmeldedaten nicht stimmen
        return Response({"error": "Ungültige Anmeldedaten"}, status=status.HTTP_400_BAD_REQUEST)


class ProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, pk, format=None):
        if not request.user.is_authenticated:
            return Response({"detail": "User not authenticated"}, status=status.HTTP_403_FORBIDDEN)

        if request.user.id != pk:
            return Response({"detail": "You can only view your own profile."}, status=status.HTTP_403_FORBIDDEN)

        try:
            profile = Profile.objects.get(user_id=pk)
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        if request.user.id != pk:
            return Response({"detail": "You can only edit your own profile."}, status=status.HTTP_403_FORBIDDEN)

        try:
            profile = Profile.objects.get(user_id=pk)
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        if request.user.id != pk:
            return Response({"detail": "You can only edit your own profile."}, status=status.HTTP_403_FORBIDDEN)

        try:
            profile = Profile.objects.get(user_id=pk)
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BusinessProfileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        business_profiles = Profile.objects.filter(type='business')
        serializer = ProfileSerializer(business_profiles, many=True)
        return Response(serializer.data)


class CustomerProfileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        customer_profiles = Profile.objects.filter(type='customer')
        serializer = ProfileSerializer(customer_profiles, many=True)
        return Response(serializer.data)

