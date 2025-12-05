from django.db import models

from apiBeneficiarios.models.beneficiarios import Beneficiario
from apiPersonasProteccion.models.personasProteccion import PersonasProteccion
from apiConsultas.models.zonas import Zonas

class ServicioPersona(models.Model):
    sp_id =  models.PositiveIntegerField(unique= True) #TODO eliminable en caso de manejar servicios localmente
    beneficiario = models.ForeignKey(Beneficiario, on_delete= models.PROTECT, related_name = 'beneficiario_persona')
    fijo = models.OneToOneField(PersonasProteccion, on_delete= models.PROTECT, related_name= 'persona_servicio') #TODO se puede dejar servicios sin pdp ?
    #Segun la logica del aplicativo, el fijo es quien se llama para activar el servicio del mismo. Si no se tiene un fijo implementado. Ningun Turno Puede ser generado
    #Por ende el correcto funcionamiento, depende de la asignación del fijo. Bien sea Manual o automatica.
    fecha_presentacion = models.DateTimeField()
    fecha_implementacion = models.DateTimeField()
    estado_servicio = models.CharField(max_length=255)
    zona = models.ForeignKey(Zonas, on_delete= models.PROTECT)
    actualizado_en = models.DateTimeField(auto_now = True)

    class Meta:
        managed = True
        db_table = 'eco_sp_asp_servicios_personas_proteccion'

    def __str__(self):
        return self.fijo.nombre_pdp