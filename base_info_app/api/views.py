from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from reviews_app.models import Review  # Importiere Review aus der reviews-App
from offers_app.models import Offer    # Importiere Offer aus der offers-App
from django.db.models import Avg

User = get_user_model()

class BaseInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Anzahl der Bewertungen
        review_count = Review.objects.count()

        # Durchschnittliche Bewertung (auf eine Dezimalstelle gerundet)
        average_rating = Review.objects.aggregate(avg_rating=Avg('rating'))['avg_rating']
        average_rating = round(average_rating, 1) if average_rating is not None else 0.0

        # Anzahl der Geschäftsnutzer
        business_profile_count = User.objects.filter(profile__type='business').count()

        # Anzahl der Angebote
        offer_count = Offer.objects.count()

        data = {
            "review_count": review_count,
            "average_rating": average_rating,
            "business_profile_count": business_profile_count,
            "offer_count": offer_count
        }
        return Response(data)