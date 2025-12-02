from django.shortcuts import render

# Create your views here.
class PDP_ViewSet(viewsets.ModelViewSet):
    queryset = PDP.objects.all()
    serializer_class = PDP_Serializer