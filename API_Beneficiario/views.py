from django.shortcuts import render
from rest_framework import viewsets
from .models import Beneficiario
from .serializer import Beneficiario_Serializer


# Create your views here.
class Beneficiario_ViewSet(viewsets.ModelViewSet):
    queryset = Beneficiario.objects.all()
    serializer_class = Beneficiario_Serializer