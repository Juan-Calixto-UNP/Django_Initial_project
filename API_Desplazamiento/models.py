from django.db import models

# Create your models here.
class Desplazamiento(models.Model):
    Esquema_extensivo = models.BooleanField(default=False)

    esquemas = ["CORPORACIÓN Y/O ASOCIACIÓN", "ESQUEMA COLECTIVO", "ESQUEMA INDIVIDUAL"]
    Tipo_esquema = models.CharField(max_length=30, choices=esquemas, default="ESQUEMA INDIVIDUAL")

    poblacion_cerrem = []

    if Tipo_esquema == "CORPORACIÓN Y/O ASOCIACIÓN":
        nombre_corporacion = models.CharField(max_length=100)
        nit_corporacion = models.CharField(max_length=20)
        celular_corporacion = models.CharField(max_length=15)
        corporacion_poblacion_cerrem = models.CharField(max_length=100,choices=poblacion_cerrem, default="")

    elif Tipo_esquema == "ESQUEMA COLECTIVO" or Tipo_esquema == "ESQUEMA INDIVIDUAL":
        nombre_representante = models.CharField(max_length=100)
        cedula_representante = models.CharField(max_length=20)
        celular_representante = models.CharField(max_length=15)
        representante_poblacion_cerrem = models.CharField(max_length=100,choices=poblacion_cerrem, default="")


