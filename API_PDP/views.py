from django.shortcuts import render
from rest_framework import viewsets
from .models import PDP
from .serializer import PDP_Serializer

# Create your views here.
class PDP_ViewSet(viewsets.ModelViewSet):
    queryset = PDP.objects.all()
    serializer_class = PDP_Serializer