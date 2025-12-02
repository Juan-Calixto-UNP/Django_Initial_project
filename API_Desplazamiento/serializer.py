from rest_framework import serializers
from .models import Desplazamiento

class Desplazamiento_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Desplazamiento
        fields = '__all__'