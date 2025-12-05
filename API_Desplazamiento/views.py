from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Desplazamiento
from .serializer import Desplazamiento_Serializer
from weasyprint import HTML
from django.template.loader import render_to_string



# Create your views here.
class Desplazamiento_ViewSet(viewsets.ModelViewSet):
    queryset = Desplazamiento.objects.all()
    serializer_class = Desplazamiento_Serializer

    def perform_create(self, serializer):
        """Override create to generate PDF after saving"""
        instance = serializer.save()
        instance.generate_pdf()
    
    def perform_update(self, serializer):
        """Override update to regenerate PDF after saving"""
        instance = serializer.save()
        instance.generate_pdf()
    
    @action(detail=True, methods=['post'])
    def regenerate_pdf(self, request, pk=None):
        """Endpoint to manually regenerate PDF"""
        desplazamiento = self.get_object()
        success = desplazamiento.generate_pdf()
        return Response({
            'status': 'success' if success else 'error',
            'message': 'PDF generated successfully' if success else 'Error generating PDF'
        })