from django.db import models
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
import uuid

# Create your models here.

class DesplazamientoPDP(models.Model):
    desplazamiento = models.ForeignKey('Desplazamiento', on_delete=models.CASCADE)
    pdp = models.ForeignKey('API_PDP.PDP', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=[('fija', 'Fija'), ('temporal', 'Temporal')])

class Desplazamiento(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    esquema_extensivo = models.BooleanField(default=False)

    TIPO_ESQUEMA_CHOICES = [
        ("CORPORACIÓN Y/O ASOCIACIÓN", "CORPORACIÓN Y/O ASOCIACIÓN"),
        ("ESQUEMA COLECTIVO", "ESQUEMA COLECTIVO"),
        ("ESQUEMA INDIVIDUAL", "ESQUEMA INDIVIDUAL"),
    ]
    tipo_esquema = models.CharField(max_length=30, choices=TIPO_ESQUEMA_CHOICES, default="ESQUEMA INDIVIDUAL")

    # Fields for corporación
    nombre_corporacion = models.CharField(max_length=100, blank=True, null=True)
    nit_corporacion = models.CharField(max_length=20, blank=True, null=True)
    celular_corporacion = models.CharField(max_length=15, blank=True, null=True)
    corporacion_poblacion_cerrem = models.CharField(max_length=100, blank=True, null=True)

    # Fields for representante
    nombre_representante = models.CharField(max_length=100, blank=True, null=True)
    cedula_representante = models.CharField(max_length=20, blank=True, null=True)
    celular_representante = models.CharField(max_length=15, blank=True, null=True)
    representante_poblacion_cerrem = models.CharField(max_length=100, blank=True, null=True)

    # Beneficiario
    beneficiario = models.ForeignKey('API_Beneficiario.Beneficiario', on_delete=models.CASCADE)

    # PDPs assigned with tipo
    pdps = models.ManyToManyField('API_PDP.PDP', through='DesplazamientoPDP', blank=True)

    # Requerimiento types
    requerimiento_terrestre = models.BooleanField(default=False)
    requerimiento_aereo = models.BooleanField(default=False)
    requerimiento_fluvial = models.BooleanField(default=False)

    # Fechas
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    # Ciudades
    ciudad_origen = models.CharField(max_length=100)
    ciudad_destino = models.CharField(max_length=100)

    # Vuelo data if aereo, as JSON
    vuelo_data = models.JSONField(blank=True, null=True)
    
    # PDF file field
    pdf_formato = models.FileField(upload_to='desplazamientos/pdfs/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def pdp_rows(self):
        return [
            {
                'nombres': dp.pdp.nombres,
                'apellidos': dp.pdp.apellidos,
                'cedula': dp.pdp.cedula,
                'telefono': dp.pdp.telefono,
                'fija': 'X' if dp.tipo == 'fija' else '',
                'temporal': 'X' if dp.tipo == 'temporal' else '',
            }
            for dp in self.desplazamientopdp_set.all()
        ]
    
    def get_template_context(self):
        """Generate context dictionary for HTML template with all required IDs"""
        return {
            # Desplazamiento data
            'esquema_extensivo': self.esquema_extensivo,
            'tipo_esquema': self.tipo_esquema,
            'requerimiento_terrestre': self.requerimiento_terrestre,
            'requerimiento_aereo': self.requerimiento_aereo,
            'requerimiento_fluvial': self.requerimiento_fluvial,
            'ciudad_origen': self.ciudad_origen,
            'ciudad_destino': self.ciudad_destino,
            'fecha_inicio_dia': self.fecha_inicio.day,
            'fecha_inicio_mes': self.fecha_inicio.month,
            'fecha_inicio_anio': self.fecha_inicio.year,
            'fecha_fin_dia': self.fecha_fin.day,
            'fecha_fin_mes': self.fecha_fin.month,
            'fecha_fin_anio': self.fecha_fin.year,
            
            # Beneficiario data
            'beneficiario_nombre': self.beneficiario.nombres if hasattr(self.beneficiario, 'nombres') else '',
            'beneficiario_apellidos': self.beneficiario.apellidos if hasattr(self.beneficiario, 'apellidos') else '',
            'beneficiario_cc': self.beneficiario.cedula if hasattr(self.beneficiario, 'cedula') else '',
            'beneficiario_celular': self.beneficiario.celular if hasattr(self.beneficiario, 'celular') else '',
            'beneficiario_cerrem': self.beneficiario.poblacion_cerrem if hasattr(self.beneficiario, 'poblacion_cerrem') else '',
            
            # Corporación/Representante data
            'nombre_corporacion': self.nombre_corporacion or '',
            'nit_corporacion': self.nit_corporacion or '',
            'celular_corporacion': self.celular_corporacion or '',
            'corporacion_cerrem': self.corporacion_poblacion_cerrem or '',
            'nombre_representante': self.nombre_representante or '',
            'cedula_representante': self.cedula_representante or '',
            'celular_representante': self.celular_representante or '',
            'representante_cerrem': self.representante_poblacion_cerrem or '',
            
            # PDP rows
            'pdp_rows': self.pdp_rows,
            'vuelo_data': self.vuelo_data or [],
        }
    
    def generate_pdf(self):
        """Generate and save PDF to model"""
        try:
            from weasyprint import HTML, CSS
            from django.template.loader import render_to_string
            
            # Get context
            context = self.get_template_context()
            
            # Render HTML
            html_string = render_to_string('Assets/Formato_desplazamientos.html', context)
            
            # Generate PDF
            pdf_file = HTML(string=html_string).write_pdf()
            
            # Save to model
            filename = f'desplazamiento_{self.id}.pdf'
            self.pdf_formato.save(filename, ContentFile(pdf_file), save=True)
            
            return True
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return False
    
    def __str__(self):
        return f"Desplazamiento {self.id} - {self.beneficiario}"


