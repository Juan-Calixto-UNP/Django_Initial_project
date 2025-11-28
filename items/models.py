from django.db import models

# Create your models here.
from django.db import models

class PersonaPDP(models.Model):
    nombre_pdp = models.CharField(max_length=200)
    cedula_pdp = models.TextField()
    serial_pdp = models.CharField(max_length=50, default='New', db_column="serial_pdp")
    
    # Bridge to SharePoint
    sharepoint_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return self.NombrePDP

    class Meta:
        #verbose_name = "PersonaPDP"
        #verbose_name_plural = "PersonasPDP"
        db_table = "persona_pdp"
        managed = False