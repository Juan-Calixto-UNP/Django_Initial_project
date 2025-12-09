from io import BytesIO
import math
import os
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from pathlib import Path
#from apiDesplazamientos.models.itinerario_model import Itinerario
#from apiDesplazamientos.models.persona_viaja_model import PersonaViaja
#from apiDesplazamientos.models.desplazamiento_model import Desplazamiento
#from apiDesplazamientos.models.destino_model import Destino
#from apiBeneficiarios.models.beneficiarios import Beneficiario
#from apiDesplazamientos.models.servicio_desplazamiento_model import ServicioDesplazamiento
#from apiPersonasProteccion.models.personasProteccion import PersonasProteccion
#from apiPersonasProteccion.models.serviciosPersonas import ServicioPersona



'''
def get_datos_crudos(desplazamiento_id):
    Obtiene los objetos relacionados al desplazamiento para poder extraer la información necesaria
    desplazamiento = Desplazamiento.objects.get(id=desplazamiento_id)
    beneficiario = desplazamiento.beneficiario
    servicio_desplazamiento = ServicioDesplazamiento.objects.get(desplazamiento=desplazamiento)
    personas_proteccion = servicio_desplazamiento.servicio.fijo

    itinerario = Itinerario.objects.prefetch_related(desplazamiento)
'''

def get_html_template():
    '''Obtiene el template HTML para el formato de desplazamiento'''
    # Django's get_template expects a path relative to template directories
    # Since Assets is in DIRS, we just need the filename
    return 'Formato_desplazamientos.html'


#-----------------------------------------------------------------------------------------------------------
#Función para determinar cuantos formatos se deben generar
#-----------------------------------------------------------------------------------------------------------
def determinar_cantidad_formatos(servicios:list):
    '''Determina la cantidad de formatos de desplazamiento a generar según la cantidad de personas de protección asociadas'''
    cantidad_formatos_pdps = math.ceil(len(servicios)/4) #Cada formato puede contener hasta 4 personas de protección
    cantidad_formatos_conexiones = math.ceil(sum(1 for servicio in servicios if servicio.get('Requerimientos', {}).get('aereo', False))/2) #Cada formato puede contener hasta 2 conexiones aéreas
    cantidad_formatos = max(cantidad_formatos_pdps, cantidad_formatos_conexiones)
    return cantidad_formatos

#-----------------------------------------------------------------------------------------------------------
#Funciones de mapeo de datos para el template
#-----------------------------------------------------------------------------------------------------------
def mapear_tipo_esquema(tipo_esquema:dict):
    '''Mapea los tipos de esquema a un diccionario para facilitar su uso en el template'''
    tipos_esquema = {
        'extensivo_nucleo_familiar': tipo_esquema.get('extensivo_nucleo_familiar', False),
        'es_colectivo': tipo_esquema.get('es_colectivo', False),
        'es_individual': tipo_esquema.get('es_individual', False)
    }
    return tipos_esquema

def mapear_datos_esquema(esquema:dict):
    '''Mapea los datos del esquema a un diccionario para facilitar su uso en el template'''
    datos_esquema = {
        'nombre_corp': esquema.get('nombre_corp', ''),
        'nit_corp': esquema.get('nit_corp', ''),
        'celular_corp': esquema.get('celular_corp', ''),
        'poblacion_cerrem': esquema.get('poblacion_cerrem', ''),
        'nombre_rep': esquema.get('nombre_rep', ''),
        'cedula_rep': esquema.get('cedula_rep', ''),
        'celular_rep': esquema.get('celular_rep', ''),
        'poblacion_cerrem_rep': esquema.get('poblacion_cerrem_rep', ''),
        'nombre_benef': esquema.get('nombre_benef', ''),
        'cedula_benef': esquema.get('cedula_benef', ''),
        'celular_benef': esquema.get('celular_benef', ''),
        'poblacion_cerrem_benef': esquema.get('poblacion_cerrem_benef', '')
    }
    return datos_esquema

def mapear_datos_requerimientos(servicios:list):
    '''Mapea los datos de los requerimientos del desplazamiento a un diccionario para facilitar su uso en el template'''
    datos_requerimientos = {
        'terrestre': any(servicio.get('Requerimientos', {}).get('terrestre', False) for servicio in servicios),
        'aereo': any(servicio.get('Requerimientos', {}).get('aereo', False) for servicio in servicios),
        'fluvial': any(servicio.get('Requerimientos', {}).get('fluvial', False) for servicio in servicios)
    }
    return datos_requerimientos

def mapear_origen_destino(itinerario:dict):
    '''Mapea los datos del itinerario a un diccionario para facilitar su uso en el template'''
    datos_itinerario = {
        'ciudad_origen': itinerario.get('ciudad_origen', ''),
        'departamento_origen': itinerario.get('departamento_origen', ''),
        'ciudad_destino': itinerario.get('ciudad_destino', ''),
        'tipo': itinerario.get('tipo', '')
    }
    return datos_itinerario

def mapear_fechas_itinerario(itinerario:dict):
    '''Mapea las fechas del itinerario a un diccionario para facilitar su uso en el template'''
    from datetime import datetime
    
    fecha_salida = itinerario.get('fecha_salida', '')
    fecha_regreso = itinerario.get('fecha_regreso', '')
    
    # Parse dates and split into components for the template
    inicio_dt = datetime.strptime(fecha_salida, '%Y-%m-%d') if fecha_salida else None
    fin_dt = datetime.strptime(fecha_regreso, '%Y-%m-%d') if fecha_regreso else None
    
    fechas_itinerario = {
        'fecha_inicio': fecha_salida,  # For the first occurrence in template
        'inicio': {
            'dia': inicio_dt.day if inicio_dt else '',
            'mes': inicio_dt.month if inicio_dt else '',
            'anio': inicio_dt.year if inicio_dt else ''
        },
        'fin': {
            'dia': fin_dt.day if fin_dt else '',
            'mes': fin_dt.month if fin_dt else '',
            'anio': fin_dt.year if fin_dt else ''
        }
    }
    return fechas_itinerario

def mapear_datos_pdp_singular(persona_proteccion:dict):
    '''Mapea los datos de la persona de protección a un diccionario para facilitar su uso en el template'''
    es_fija = persona_proteccion.get('fijo', True)
    datos_persona_proteccion = {
        'nombres_pdp': persona_proteccion.get('nombre_pdp', ''),
        'apellidos_pdp': persona_proteccion.get('apellido_pdp', ''),
        'cedula_pdp': persona_proteccion.get('cedula_pdp', ''),
        'telefono_contacto': persona_proteccion.get('numero_contacto', ''),
        'fija': es_fija,
        'temporal': not es_fija  # Add temporal field (opposite of fija)
    }
    return datos_persona_proteccion

def mapear_datos_pdps(servicios:list):
    '''Determina los datos a llenar por cada PDP y si aereo==true llama a la funcion mapear_datos_tiquetes'''
    datos_pdp_list = []
    for servicio in servicios:
        datos_pdp = mapear_datos_pdp_singular(servicio)
        datos_pdp_list.append(datos_pdp)
    return datos_pdp_list

def mapear_datos_pasajeros(servicios:list):
    '''Mapea los datos de los pasajeros a un diccionario para facilitar su uso en el template.
    aereo=True in Requerimientos'''
    datos_pasajeros = []
    
    # Add passengers who need aerial tickets
    for servicio in servicios:
        if servicio.get('Requerimientos', {}).get('aereo', False):
            pasajero = {
                'nombres': servicio.get('nombre_pdp', ''),  # Template expects 'nombres' not 'nombres_pdp'
                'apellidos': servicio.get('apellido_pdp', ''),  # Template expects 'apellidos' not 'apellidos_pdp'
                'cedula': servicio.get('cedula_pdp', ''),  # Template expects 'cedula' not 'cedula_pdp'
                'telefono_contacto': servicio.get('numero_contacto', '')
            }
            datos_pasajeros.append(pasajero)
    
    # Fill remaining rows with empty entries (up to 4 total)
    while len(datos_pasajeros) < 4:
        datos_pasajeros.append({
            'nombres': '',
            'apellidos': '',
            'cedula': '',
            'telefono_contacto': ''
        })
    
    return datos_pasajeros
    

def mapear_datos_tiquetes_ida_regreso(servicios:list):
    '''Mapea solo IDA y REGRESO desde TODOS los servicios (para mostrar en todas las páginas)
    Args:
        servicios: lista completa de servicios
    Returns:
        dict: diccionario con solo ida y regreso
    '''
    # Recopilar todos los vuelos de servicios con aereo=True
    vuelos = []
    for servicio in servicios:
        if servicio.get('Requerimientos', {}).get('aereo', False):
            vuelo = {
                'fecha': servicio.get('fecha_vuelo', ''),
                'hora': servicio.get('hora_vuelo', ''),
                'origen': servicio.get('origen', ''),
                'destino': servicio.get('destino', ''),
                'aerolinea': servicio.get('aerolinea', ''),
                'vuelo': servicio.get('numero_vuelo', '')
            }
            vuelos.append(vuelo)
    
    # Estructura base para ida y regreso
    resultado = {
        'ida': {
            'fecha': '',
            'hora': '',
            'origen': '',
            'destino': '',
            'aerolinea': '',
            'vuelo': ''
        },
        'regreso': {
            'fecha': '',
            'hora': '',
            'origen': '',
            'destino': '',
            'aerolinea': '',
            'vuelo': ''
        }
    }
    
    # Asignar primer vuelo como IDA
    if len(vuelos) > 0:
        resultado['ida'] = vuelos[0]
    
    # Asignar último vuelo como REGRESO
    if len(vuelos) > 1:
        resultado['regreso'] = vuelos[-1]
    
    return resultado

def mapear_datos_conexiones(servicios:list):
    '''Mapea solo las CONEXIONES desde los servicios de una página específica
    Args:
        servicios: lista de servicios de la página actual
    Returns:
        list: lista con hasta 2 conexiones
    '''
    # Recopilar vuelos de servicios con aereo=True de esta página
    vuelos = []
    for servicio in servicios:
        if servicio.get('Requerimientos', {}).get('aereo', False):
            vuelo = {
                'fecha': servicio.get('fecha_vuelo', ''),
                'hora': servicio.get('hora_vuelo', ''),
                'origen': servicio.get('origen', ''),
                'destino': servicio.get('destino', ''),
                'aerolinea': servicio.get('aerolinea', ''),
                'vuelo': servicio.get('numero_vuelo', '')
            }
            vuelos.append(vuelo)
    
    # Estructura base para conexiones (siempre 2 slots)
    conexiones = [
        {
            'fecha': '',
            'hora': '',
            'origen': '',
            'destino': '',
            'aerolinea': '',
            'vuelo': ''
        },
        {
            'fecha': '',
            'hora': '',
            'origen': '',
            'destino': '',
            'aerolinea': '',
            'vuelo': ''
        }
    ]
    
    # Asignar vuelos como conexiones (hasta 2)
    for i, vuelo in enumerate(vuelos):
        if i < 2:
            conexiones[i] = vuelo
    
    return conexiones

#-----------------------------------------------------------------------------------------------------------

def formatear_contexto_por_pagina(desplazamiento:dict, pagina:int, total_paginas:int):
    '''Formatea el contexto para una página específica del PDF
    Args:
        desplazamiento: diccionario con todos los datos del desplazamiento
        pagina: número de página actual (1-indexed)
        total_paginas: total de páginas a generar
    Returns:
        dict: contexto formateado para la página específica
    '''
    servicios = desplazamiento.get('Servicios', [])
    
    # Calcular el rango de servicios para esta página (4 por página)
    inicio = (pagina - 1) * 4
    fin = min(inicio + 4, len(servicios))
    servicios_pagina = servicios[inicio:fin]
    
    # Completar con servicios vacíos si es necesario (hasta 4)
    while len(servicios_pagina) < 4:
        servicios_pagina.append({
            'nombre_pdp': '',
            'apellido_pdp': '',
            'cedula_pdp': '',
            'numero_contacto': '',
            'fijo': True,
            'Requerimientos': {
                'terrestre': False,
                'aereo': False,
                'fluvial': False
            }
        })
    
    # El contexto base se repite en todas las páginas
    context = {
        'tipo_esquema': mapear_tipo_esquema(desplazamiento.get('Tipo_esquema', {})),
        'datos_esquema': mapear_datos_esquema(desplazamiento.get('Datos_esquema', {})),
        'requerimientos_generales': mapear_datos_requerimientos(servicios),  # Todos los servicios
        'origen_destino': mapear_origen_destino(desplazamiento.get('Itinerario', {})),
        'fechas': mapear_fechas_itinerario(desplazamiento.get('Itinerario', {})),
        'pdps': mapear_datos_pdps(servicios_pagina),  # Solo los de esta página
        'pagina_actual': pagina,
        'total_paginas': total_paginas
    }
    
    # La tabla de pasajeros siempre se muestra (con los PDPs de esta página que requieren aéreo)
    # IDA y REGRESO se muestran en todas las páginas (desde todos los servicios)
    # CONEXIÓN varía por página (desde servicios de esta página)
    ida_regreso = mapear_datos_tiquetes_ida_regreso(servicios)  # Todos los servicios
    conexiones = mapear_datos_conexiones(servicios_pagina)  # Servicios de esta página
    
    context['tiquetes'] = {
        'pasajeros': mapear_datos_pasajeros(servicios_pagina),  # Pasajeros de esta página (siempre 4 filas)
        'segmentos': {
            'ida': ida_regreso['ida'],
            'conexiones': conexiones,
            'regreso': ida_regreso['regreso']
        }
    }
    
    return context


#Función principal de renderizado del PDF
def render_desplazamiento_pdf(desplazamiento:dict):
    '''Con el id del desplazamiento obtiene la información del beneficiario y la(s) persona(s) de protección
    asociada(s) para generar el PDF del formato de desplazamiento'''

    '''Los datos vendrán de un serializador que se espera tendrá la información de la siguiente manera:
    desplazamiento = {
        "id": "12345",
        "Tipo_esquema": {
            "extensivo_nucleo_familiar": True,
            "es_colectivo": False,
            "es_individual": False
        },
        "Datos_esquema": {
            "nombre_corp": "Corporación Ejemplo",
            "nit_corp": "900123456-7",
            "celular_corp": "3001234567",
            "poblacion_cerrem": "Población Ejemplo",
            "nombre_rep": "Juan Pérez",
            "cedula_rep": "12345678",
            "celular_rep": "3007654321",
            "poblacion_cerrem_rep": "Población Representante",
            "nombre_benef": "Ana Gómez",
            "cedula_benef": "87654321",
            "celular_benef": "3001122334",
            "poblacion_cerrem_benef": "Población Beneficiario"
        },
        "Servicios":[
            {
                "nombre_pdp": "Carlos",
                "apellido_pdp": "López",
                "cedula_pdp": "11223344",
                "numero_contacto": "3009988776",
                "fijo": True,
                "Requerimientos": {
                    "terrestre": True,
                    "aereo": False,
                    "fluvial": False
                }
            },
            {
                "nombre_pdp": "María",
                "apellido_pdp": "Rodríguez",
                "cedula_pdp": "55667788",
                "numero_contacto": "3008877665",
                "fijo": False,
                "Requerimientos": {
                    "terrestre": False,
                    "aereo": True,
                    "fluvial": False
                },
                "Tiquete_aereo": {
                    "aerolinea": "Aerolínea Ejemplo",
                    "numero_vuelo": "AE1234",
                    "fecha_vuelo": "2024-01-16",
                    "hora_vuelo": "10:00",
                    "origen": "Aeropuerto Ejemplo 1",
                    "destino": "Aeropuerto Ejemplo 2"
                }
            }
        ],
        "Itinerario": {
            "ciudad_origen": "Bogotá",
            "departamento_origen": "Cundinamarca",
            "ciudad_destino": "Medellín",
            "tipo": "Temporal",
            "fecha_salida": "2024-01-15",
            "fecha_regreso": "2024-01-20"
        }
    }'''

    servicios = desplazamiento.get('Servicios', [])
    cantidad_formatos = determinar_cantidad_formatos(servicios)
    desplazamiento_id = desplazamiento.get('id', 'desconocido')
    
    # Cargar el template HTML
    template = get_template(get_html_template())
    
    # Crear el response para el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="desplazamiento_{desplazamiento_id}.pdf"'
    
    # Buffer para acumular el HTML de todas las páginas
    html_completo = ""
    
    # Generar el HTML para cada página
    for i in range(1, cantidad_formatos + 1):
        context = formatear_contexto_por_pagina(desplazamiento, i, cantidad_formatos)
        html_pagina = template.render(context)
        
        # Wrap each page with proper page break for xhtml2pdf
        if i > 1:
            # Add page break before subsequent pages
            html_completo += '<pdf:nextpage />'
        
        html_completo += html_pagina
    
    # Generar el PDF desde el HTML completo
    pisa_status = pisa.CreatePDF(
        html_completo, 
        dest=response, 
        encoding='UTF-8',
        link_callback=lambda uri, rel: uri  # Simple callback for any resources
    )
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response