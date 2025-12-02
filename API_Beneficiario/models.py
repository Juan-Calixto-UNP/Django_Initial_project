from django.db import models

# Create your models here.
class Beneficiario(models.Model):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=15)
    pdp_fija = models.ForeignKey('API_PDP.PDP', on_delete=models.CASCADE)