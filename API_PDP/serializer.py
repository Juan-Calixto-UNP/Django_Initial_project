from rest_framework import serializers
from .models import PDP

class PDP_Serializer(serializers.ModelSerializer):
    class Meta:
        model = PDP
        fields = '__all__'