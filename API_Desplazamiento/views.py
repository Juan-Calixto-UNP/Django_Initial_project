from django.shortcuts import render
from rest_framework import viewsets
from .models import Desplazamiento
from .serializer import Desplazamiento_Serializer

# Create your views here.
class Desplazamiento_ViewSet(viewsets.ModelViewSet):
    queryset = Desplazamiento.objects.all()
    serializer_class = Desplazamiento_Serializer