from rest_framework import serializers
from rest_framework.reverse import reverse
from ..models import Offer, OfferDetail

# Serializer für die GET-Anfragen der OfferDetails
class OfferDetailGETSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']

    def get_url(self, obj):
        request = self.context.get("request")
        return reverse("offer-detail-detail", args=[obj.id], request=request)
    

# Serializer für die vollständigen Details eines Angebotsdetails (GET /api/offerdetails/{id}/)
class OfferDetailFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferDetail
        fields = ['id', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type']


# Serializer für die Liste der Angebote (GET /api/offers/)
class OfferListSerializer(serializers.ModelSerializer):
    details = OfferDetailGETSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time',
            'user_details'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'min_price', 'min_delivery_time', 'user_details']

    def get_min_price(self, obj):
        if obj.details.exists():
            return min(detail.price for detail in obj.details.all())
        return None

    def get_min_delivery_time(self, obj):
        if obj.details.exists():
            return min(detail.delivery_time_in_days for detail in obj.details.all())
        return None

    def get_user_details(self, obj):
        user = obj.user
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
        }

# Serializer für die Details eines einzelnen Angebots (GET /api/offers/{id}/)
class OfferDetailSerializer(serializers.ModelSerializer):
    details = OfferDetailGETSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'min_price', 'min_delivery_time']

    def get_min_price(self, obj):
        if obj.details.exists():
            return min(detail.price for detail in obj.details.all())
        return None

    def get_min_delivery_time(self, obj):
        if obj.details.exists():
            return min(detail.delivery_time_in_days for detail in obj.details.all())
        return None

# Serializer für die POST-Anfragen (unverändert)
class OfferDetailPOSTSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferDetail
        fields = ['id', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type']

class OfferSerializer(serializers.ModelSerializer):
    details = OfferDetailPOSTSerializer(many=True)

    class Meta:
        model = Offer
        fields = ['id', 'title', 'image', 'description', 'details']

    def validate(self, data):
            details_data = data.get('details', [])
            
            # Nur bei POST-Anfragen prüfen, ob genau drei Details vorhanden sind
            if self.context['request'].method == 'POST':
                if len(details_data) != 3:
                    raise serializers.ValidationError({"details": "Exactly three offer details must be provided."})
                
                types = {detail['offer_type'] for detail in details_data}
                if types != {'basic', 'standard', 'premium'}:
                    raise serializers.ValidationError({"details": "Offer details must include one each of basic, standard, and premium."})
                
                for detail in details_data:
                    if not detail.get('features') or len(detail['features']) == 0:
                        raise serializers.ValidationError({"features": "Each offer detail must have at least one feature."})
            
            return data

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        user = self.context['request'].user
        validated_data.pop('user', None)
        offer = Offer.objects.create(user=user, **validated_data)
        
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        
        return offer

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)
        instance.title = validated_data.get('title', instance.title)
        instance.image = validated_data.get('image', instance.image)
        instance.description = validated_data.get('description', instance.description)
        instance.status = validated_data.get('status', instance.status)
        instance.save()

        if details_data:
            for detail_data in details_data:
                offer_type = detail_data.get('offer_type')
                try:
                    detail = instance.details.get(offer_type=offer_type)
                    detail.title = detail_data.get('title', detail.title)
                    detail.revisions = detail_data.get('revisions', detail.revisions)
                    detail.delivery_time_in_days = detail_data.get('delivery_time_in_days', detail.delivery_time_in_days)
                    detail.price = detail_data.get('price', detail.price)
                    detail.features = detail_data.get('features', detail.features)
                    detail.save()
                except OfferDetail.DoesNotExist:
                    pass

        return instance