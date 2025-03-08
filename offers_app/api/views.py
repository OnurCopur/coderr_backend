from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Min
from django.http import Http404
from rest_framework.exceptions import ValidationError
from ..models import Offer, OfferDetail
from .serializers import OfferSerializer, OfferDetailSerializer, OfferListSerializer, OfferDetailFullSerializer
from .pagination import OfferPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class OfferListCreateView(generics.ListCreateAPIView):
    queryset = Offer.objects.all().order_by('-updated_at')
    permission_classes = [AllowAny]  
    authentication_classes = [TokenAuthentication]
    pagination_class = OfferPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user']  # Für creator_id
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']  
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return OfferListSerializer
        return OfferSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(
            min_price=Min('details__price'),
            min_delivery_time=Min('details__delivery_time_in_days')
        )
        
        # Filter
        creator_id = self.request.query_params.get('creator_id')
        min_price = self.request.query_params.get('min_price')
        max_delivery_time = self.request.query_params.get('max_delivery_time')
        
        if creator_id:
            qs = qs.filter(user__id=creator_id)
        if min_price:
            try:
                min_price = float(min_price)
                qs = qs.filter(min_price__gte=min_price)
            except ValueError:
                raise ValidationError({"min_price": "Ungültiger Wert. Erwartet wird eine Zahl."})
        
        if max_delivery_time:
            try:
                max_delivery_time = int(max_delivery_time)
                qs = qs.filter(min_delivery_time__lte=max_delivery_time)
            except ValueError:
                raise ValidationError({"max_delivery_time": "Ungültiger Wert. Erwartet wird eine ganze Zahl."})
        
        return qs

    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'profile') or self.request.user.profile.type != 'business':
            raise PermissionDenied("Only business users can create offers.")
        serializer.save(user=self.request.user)  # Der Benutzer wird im Serializer gesetzt


class OfferDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferDetailSerializer  
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return OfferSerializer  # Verwende OfferSerializer für PATCH-Anfragen
        return OfferDetailSerializer

    def get_object(self):
        try:
            offer = Offer.objects.get(pk=self.kwargs['pk'])
        except Offer.DoesNotExist:
            raise Http404

        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            if not (self.request.user.is_staff or offer.user == self.request.user):
                raise PermissionDenied("You do not have permission to modify this offer.")
        return offer



class OfferDetailDetailView(generics.RetrieveAPIView):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
