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

import Services.formato_desplazamiento_rendering


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
    for index in range(1, 6):
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
    from django.http import HttpResponse
    from django.template.loader import get_template

    Diccionario_ejemplo = build_sample_payload()
    
    # Save rendered HTML for debugging
    output_dir = BASE_DIR / 'output'
    output_dir.mkdir(exist_ok=True)
    
    try:
        html_rendered = Services.formato_desplazamiento_rendering.render_desplazamiento_pdf(Diccionario_ejemplo)
        
        # Save the PDF
        pdf_path = output_dir / 'formato_desplazamiento.pdf'
        pdf_path.write_bytes(html_rendered.content)
        print(f'PDF generado exitosamente en: {pdf_path}')
        
    except Exception as e:
        print(f'Error al generar PDF: {e}')
        
        # Generate HTML for debugging
        print('\nGenerando HTML para debug...')
        from Services.formato_desplazamiento_rendering import (
            formatear_contexto_por_pagina,
            determinar_cantidad_formatos,
            get_html_template
        )
        
        servicios = Diccionario_ejemplo.get('Servicios', [])
        cantidad_formatos = determinar_cantidad_formatos(servicios)
        
        template = get_template(get_html_template())
        
        for i in range(1, cantidad_formatos + 1):
            context = formatear_contexto_por_pagina(Diccionario_ejemplo, i, cantidad_formatos)
            html_pagina = template.render(context)
            
            html_path = output_dir / f'debug_page_{i}.html'
            html_path.write_text(html_pagina, encoding='utf-8')
            print(f'HTML página {i} guardado en: {html_path}')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="formato_desplazamiento.pdf"'

if __name__ == '__main__':
    main()
