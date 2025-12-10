"""Prueba manual del generador de formatos de desplazamiento.

Este script crea un diccionario de ejemplo con mas de cuatro personas de
proteccion (PDP) y lo envia a la funcion ``render_desplazamiento_pdf`` para
verificar que se generan multiples archivos cuando aplica.
"""
from __future__ import annotations
import Services.formato_desplazamiento_rendering
from io import BytesIO
import sys
from pathlib import Path
from typing import List

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Permite importar ``services.html_rendering`` ubicado dentro de ``.venv``.
BASE_DIR = Path(__file__).resolve().parent
SERVICES_DIR = BASE_DIR / '.venv'
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))




def _ensure_django_ready() -> None:
    """Configura un entorno minimo de Django si aun no existe."""
    if settings.configured:
        return

    settings.configure(
        INSTALLED_APPS=[],
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
                'DIRS': [str(BASE_DIR / 'Assets')],
                'OPTIONS': {},
            }
        ],
    )

    try:
        import django

        django.setup()
    except ImproperlyConfigured:
        # Si no existe el modulo de settings "real" del proyecto, la
        # configuracion minima anterior es suficiente para esta prueba manual.
        pass


def build_sample_payload() -> dict:
    """Construye un desplazamiento de ejemplo con PDPs con vuelos."""
    # Definir vuelos compartidos (Ida y Regreso no se duplican)
    vuelo_ida = {
        'tipo': 'Ida',
        'aerolinea': 'Avianca',
        'numero_vuelo': 'AV120',
        'fecha_vuelo': '2025-02-15',
        'hora_vuelo': '06:30',
        'origen': 'Bogota',
        'destino': 'Medellin',
    }
    
    vuelo_regreso = {
        'tipo': 'Regreso',
        'aerolinea': 'Avianca',
        'numero_vuelo': 'AV121',
        'fecha_vuelo': '2025-02-20',
        'hora_vuelo': '18:45',
        'origen': 'Medellin',
        'destino': 'Bogota',
    }
    
    # Vuelos de conexión opcionales
    vuelo_conexion = {
        'tipo': 'Conexion',
        'aerolinea': 'LATAM',
        'numero_vuelo': 'LA205',
        'fecha_vuelo': '2025-02-16',
        'hora_vuelo': '12:15',
        'origen': 'Medellin',
        'destino': 'Cali',
    }
    
    servicios: List[dict] = []
    for index in range(1, 2):
        requiere_aereo = index % 2 == 1
        
        # Datos básicos del servicio
        servicio = {
            'nombre_pdp': f'Nombre {index}',
            'apellido_pdp': f'Apellido {index}',
            'cedula_pdp': f'10{index:02d}2299',
            'numero_contacto': f'30000000{index}',
            'fijo': index % 2 == 0,
            'Requerimientos': {
                'terrestre': True,
                'aereo': requiere_aereo,
                'fluvial': False,
            },
        }
        
        # Si requiere aéreo, agregar vuelos
        if requiere_aereo:
            servicio['vuelos'] = [
                vuelo_ida,
                vuelo_regreso,
            ]
            # El primer PDP con aéreo también tiene una conexión
            if index == 1:
                servicio['vuelos'].append(vuelo_conexion)
        
        servicios.append(servicio)

    return {
        'id': 'demo',
        'Tipo_esquema': {
            'extensivo_nucleo_familiar': True,
            'es_corporacion': True,
            'es_colectivo': False,
            'es_individual': False,
        },
        'Datos_esquema': {
            'nombre_corp': 'Corporacion Ejemplo',
            'nit_corp': '900123456-7',
            'celular_corp': '3001234567',
            'poblacion_cerrem': 'Poblacion Ejemplo',
            'nombre_rep': 'Juan Perez',
            'cedula_rep': '11223344',
            'celular_rep': '3000000000',
            'nombre_benef': 'Ana Gomez',
            'cedula_benef': '99887766',
            'celular_benef': '3112223344',
        },
        
        'Itinerario': {
            'ciudad_origen': 'Bogota',
            'departamento_origen': 'Cundinamarca',
            'ciudad_destino': 'Medellin',
            'tipo': 'Ida y regreso',
            'fecha_salida': '2025-01-15',
            'fecha_regreso': '2025-01-20',
        },
        'Servicios': servicios,
        }
        

def main() -> None:
    _ensure_django_ready()

    diccionario_ejemplo = build_sample_payload()
    pdf_file = Services.formato_desplazamiento_rendering.render_desplazamiento_pdf(diccionario_ejemplo)

    # Guardar el PDF generado en un archivo para inspeccionarlo.
    #print(diccionario_ejemplo)
    print('PDF de desplazamiento generado: Formato_desplazamiento_llenado.pdf')

if __name__ == '__main__':
    main()
