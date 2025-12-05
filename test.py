"""Prueba manual del generador de formatos de desplazamiento.

Este script crea un diccionario de ejemplo con mas de cuatro personas de
proteccion (PDP) y lo envia a la funcion ``render_desplazamiento_pdf`` para
verificar que se generan multiples archivos cuando aplica.
"""
from __future__ import annotations

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

from services.html_rendering import (  # pylint: disable=wrong-import-position
    DEFAULT_TEMPLATE_PATH,
    render_desplazamiento_pdf,
)


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
    """Construye un desplazamiento de ejemplo con seis PDP."""
    servicios: List[dict] = []
    for index in range(1, 4):
        requiere_aereo = index % 2 == 1
        servicios.append(
            {
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
                **(
                    {
                        'aerolinea': 'Avianca',
                        'numero_vuelo': f'AV{120 + index}',
                        'fecha_vuelo': f'2025-02-{10 + index:02d}',
                        'hora_vuelo': f'{6 + index:02d}:30',
                        'origen': 'Bogota',
                        'destino': 'Medellin',
                    }
                    if requiere_aereo
                    else {}
                ),
            }
        )

    return {
        'id': 'demo',
        'Tipo_esquema': {
            'extensivo_nucleo_familiar': True,
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
            'poblacion_cerrem_rep': 'Lider Social',
            'nombre_benef': 'Ana Gomez',
            'cedula_benef': '99887766',
            'celular_benef': '3112223344',
            'poblacion_cerrem_benef': 'Beneficiario',
        },
        'Requerimientos': {
            'terrestre': True,
            'aereo': True,
            'fluvial': False,
        },
        'Itinerario': {
            'ciudad_origen': 'Bogota',
            'departamento_origen': 'Cundinamarca',
            'ciudad_destino': 'Medellin',
            'tipo': 'Ida y regreso',
            'fecha_salida': '2025-01-15',
            'fecha_regreso': '2025-01-20',
        },
        'Tiquetes': {
            'pasajeros': [
                {
                    'nombres': 'Carlos',
                    'apellidos': 'Lopez',
                    'cedula': '12345678',
                    'telefono_contacto': '3001112233',
                },
                {
                    'nombres': 'Maria',
                    'apellidos': 'Rodriguez',
                    'cedula': '87654321',
                    'telefono_contacto': '3004445566',
                },
            ],
            'ida': {
                'fecha': '2025-01-15',
                'hora': '08:00',
                'origen': 'Bogota',
                'destino': 'Medellin',
                'aerolinea': 'Avianca',
                'vuelo': 'AV123',
            },
            'conexiones': [
                {
                    'fecha': '2025-01-15',
                    'hora': '10:00',
                    'origen': 'Medellin',
                    'destino': 'Quibdo',
                    'aerolinea': 'Satena',
                    'vuelo': 'SA456',
                }
            ],
            'regreso': {
                'fecha': '2025-01-20',
                'hora': '14:30',
                'origen': 'Medellin',
                'destino': 'Bogota',
                'aerolinea': 'Avianca',
                'vuelo': 'AV321',
            },
        },
        'Servicios': servicios,
    }


def main() -> None:
    _ensure_django_ready()
    payload = build_sample_payload()

    print('Generando PDFs de prueba...')
    responses = render_desplazamiento_pdf(payload, template_path=DEFAULT_TEMPLATE_PATH)
    print(f'Se generaron {len(responses)} formato(s).')

    output_dir = BASE_DIR / 'output'
    output_dir.mkdir(exist_ok=True)

    for index, response in enumerate(responses, start=1):
        disposition = response.get('Content-Disposition', '')
        file_name = ''
        if 'filename=' in disposition:
            file_name = disposition.split('filename=')[-1].strip('"')
        if not file_name:
            file_name = f'desplazamiento_{payload.get("id", "sin_id")}_{index}.pdf'

        output_path = output_dir / file_name
        output_path.write_bytes(response.content)
        print(f'- Archivo guardado en: {output_path}')

    print('Prueba finalizada. Revise la carpeta "output" para ver los PDFs.')


if __name__ == '__main__':
    main()
