from rest_framework import serializers
from .models import PersonaPDP

class PersonaPDP_Serializer(serializers.ModelSerializer):
    class Meta:
        model = PersonaPDP
        fields = ('nombre_pdp', 'cedula_pdp', 'serial_pdp', 'sharepoint_id')
        read_only_fields = ('sharepoint_id',)