from rest_framework import serializers
from .models import Beneficiario

class Beneficiario_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiario
        fields = '__all__'