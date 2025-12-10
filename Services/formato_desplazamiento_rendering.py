from io import BytesIO
import math
import os
from django.http import HttpResponse
from pathlib import Path
from PyPDFForm import PdfWrapper
#from apiDesplazamientos.models.itinerario_model import Itinerario
#from apiDesplazamientos.models.persona_viaja_model import PersonaViaja
#from apiDesplazamientos.models.desplazamiento_model import Desplazamiento
#from apiDesplazamientos.models.destino_model import Destino
#from apiBeneficiarios.models.beneficiarios import Beneficiario
#from apiDesplazamientos.models.servicio_desplazamiento_model import ServicioDesplazamiento
#from apiPersonasProteccion.models.personasProteccion import PersonasProteccion
#from apiPersonasProteccion.models.serviciosPersonas import ServicioPersona


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


def get_pdf_template_path():
    '''Retorna la ruta al archivo PDF template'''
    # Ajusta esta ruta según donde esté tu PDF template
    base_path = Path(__file__).parent.parent
    template_path = base_path / 'Assets' / 'Formato_desplazamientos.pdf'
    return str(template_path)


def mapear_campos_pdf(context:dict, pagina:int):
    '''Mapea los datos del contexto a los nombres de campos del formulario PDF
    Args:
        context: diccionario con los datos formateados
        pagina: número de página para incluir en campos dinámicos
    Returns:
        dict: diccionario con nombres de campos PDF como keys y valores correspondientes
    '''
    campos = {}
    
    # Tipo de esquema (checkboxes)
    campos['extensivo_nucleo_familiar'] = 'X' if context['tipo_esquema']['extensivo_nucleo_familiar'] else ''
    campos['es_colectivo'] = 'X' if context['tipo_esquema']['es_colectivo'] else ''
    campos['es_individual'] = 'X' if context['tipo_esquema']['es_individual'] else ''
    
    # Datos del esquema
    esquema = context['datos_esquema']
    campos['nombre_corp'] = esquema['nombre_corp']
    campos['nit_corp'] = esquema['nit_corp']
    campos['celular_corp'] = esquema['celular_corp']
    campos['poblacion_cerrem'] = esquema['poblacion_cerrem']
    campos['nombre_rep'] = esquema['nombre_rep']
    campos['cedula_rep'] = esquema['cedula_rep']
    campos['celular_rep'] = esquema['celular_rep']
    campos['poblacion_cerrem_rep'] = esquema['poblacion_cerrem_rep']
    campos['nombre_benef'] = esquema['nombre_benef']
    campos['cedula_benef'] = esquema['cedula_benef']
    campos['celular_benef'] = esquema['celular_benef']
    campos['poblacion_cerrem_benef'] = esquema['poblacion_cerrem_benef']
    
    # Requerimientos generales
    req = context['requerimientos_generales']
    campos['req_terrestre'] = 'X' if req['terrestre'] else ''
    campos['req_aereo'] = 'X' if req['aereo'] else ''
    campos['req_fluvial'] = 'X' if req['fluvial'] else ''
    
    # Origen y destino
    origen_destino = context['origen_destino']
    campos['ciudad_origen'] = origen_destino['ciudad_origen']
    campos['departamento_origen'] = origen_destino['departamento_origen']
    campos['ciudad_destino'] = origen_destino['ciudad_destino']
    campos['tipo_desplazamiento'] = origen_destino['tipo']
    
    # Fechas
    fechas = context['fechas']
    campos['dia_inicio'] = str(fechas['inicio']['dia'])
    campos['mes_inicio'] = str(fechas['inicio']['mes'])
    campos['anio_inicio'] = str(fechas['inicio']['anio'])
    campos['dia_fin'] = str(fechas['fin']['dia'])
    campos['mes_fin'] = str(fechas['fin']['mes'])
    campos['anio_fin'] = str(fechas['fin']['anio'])
    
    # PDPs (4 por página)
    for i, pdp in enumerate(context['pdps'], 1):
        campos[f'pdp_{i}_nombres'] = pdp['nombres_pdp']
        campos[f'pdp_{i}_apellidos'] = pdp['apellidos_pdp']
        campos[f'pdp_{i}_cedula'] = pdp['cedula_pdp']
        campos[f'pdp_{i}_telefono'] = pdp['telefono_contacto']
        campos[f'pdp_{i}_fija'] = 'X' if pdp['nombres_pdp'] and pdp['fija'] else ''
        campos[f'pdp_{i}_temporal'] = 'X' if pdp['nombres_pdp'] and pdp['temporal'] else ''
    
    # Pasajeros (4 filas)
    for i, pasajero in enumerate(context['tiquetes']['pasajeros'], 1):
        campos[f'pasajero_{i}_nombres'] = pasajero['nombres']
        campos[f'pasajero_{i}_apellidos'] = pasajero['apellidos']
        campos[f'pasajero_{i}_cedula'] = pasajero['cedula']
        campos[f'pasajero_{i}_telefono'] = pasajero['telefono_contacto']
    
    # Segmentos de vuelo (IDA, CONEXIÓN 1, CONEXIÓN 2, REGRESO)
    segmentos = context['tiquetes']['segmentos']
    
    # IDA
    campos['ida_fecha'] = segmentos['ida']['fecha']
    campos['ida_hora'] = segmentos['ida']['hora']
    campos['ida_origen'] = segmentos['ida']['origen']
    campos['ida_destino'] = segmentos['ida']['destino']
    campos['ida_aerolinea'] = segmentos['ida']['aerolinea']
    campos['ida_vuelo'] = segmentos['ida']['vuelo']
    
    # CONEXIÓN 1
    campos['conexion_1_fecha'] = segmentos['conexiones'][0]['fecha']
    campos['conexion_1_hora'] = segmentos['conexiones'][0]['hora']
    campos['conexion_1_origen'] = segmentos['conexiones'][0]['origen']
    campos['conexion_1_destino'] = segmentos['conexiones'][0]['destino']
    campos['conexion_1_aerolinea'] = segmentos['conexiones'][0]['aerolinea']
    campos['conexion_1_vuelo'] = segmentos['conexiones'][0]['vuelo']
    
    # CONEXIÓN 2
    campos['conexion_2_fecha'] = segmentos['conexiones'][1]['fecha']
    campos['conexion_2_hora'] = segmentos['conexiones'][1]['hora']
    campos['conexion_2_origen'] = segmentos['conexiones'][1]['origen']
    campos['conexion_2_destino'] = segmentos['conexiones'][1]['destino']
    campos['conexion_2_aerolinea'] = segmentos['conexiones'][1]['aerolinea']
    campos['conexion_2_vuelo'] = segmentos['conexiones'][1]['vuelo']
    
    # REGRESO
    campos['regreso_fecha'] = segmentos['regreso']['fecha']
    campos['regreso_hora'] = segmentos['regreso']['hora']
    campos['regreso_origen'] = segmentos['regreso']['origen']
    campos['regreso_destino'] = segmentos['regreso']['destino']
    campos['regreso_aerolinea'] = segmentos['regreso']['aerolinea']
    campos['regreso_vuelo'] = segmentos['regreso']['vuelo']
    
    return campos


#Función principal de renderizado del PDF
def render_desplazamiento_pdf(desplazamiento:dict):
    '''Con el id del desplazamiento obtiene la información del beneficiario y la(s) persona(s) de protección
    asociada(s) para generar el PDF del formato de desplazamiento usando PyPDFForm'''

    servicios = desplazamiento.get('Servicios', [])
    cantidad_formatos = determinar_cantidad_formatos(servicios)
    desplazamiento_id = desplazamiento.get('id', 'desconocido')
    
    # Obtener ruta al PDF template
    template_path = get_pdf_template_path()
    
    # Verificar que existe el template
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"No se encuentra el PDF template en: {template_path}")
    
    # Lista para almacenar los PDFs generados
    pdfs_generados = []
    
    # Generar un PDF por cada página necesaria
    for pagina in range(1, cantidad_formatos + 1):
        # Formatear el contexto para esta página
        context = formatear_contexto_por_pagina(desplazamiento, pagina, cantidad_formatos)
        
        # Mapear los datos a los campos del PDF
        campos = mapear_campos_pdf(context, pagina)
        
        # Cargar el template y llenar los campos
        pdf = PdfWrapper(template_path)
        pdf = pdf.fill(campos,flatten=True)
        
        # Guardar el PDF en memoria
        pdf_stream = BytesIO()
        pdf.write(pdf_stream)
        pdf_stream.seek(0)
        
        pdfs_generados.append(pdf_stream)
    
    # Si hay múltiples PDFs, unirlos en uno solo
    if len(pdfs_generados) > 1:
        # Cargar el primer PDF
        pdf_final = PdfWrapper(pdfs_generados[0])
        
        # Agregar los demás PDFs
        for pdf_stream in pdfs_generados[1:]:
            pdf_stream.seek(0)
            pdf_a_agregar = PdfWrapper(pdf_stream)
            pdf_final = pdf_final + pdf_a_agregar
    else:
        # Solo hay un PDF
        pdf_final = PdfWrapper(pdfs_generados[0])
    
    # Crear el response HTTP con el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="desplazamiento_{desplazamiento_id}.pdf"'
    
    # Escribir el PDF final al response
    pdf_final.write(response)
    
    return response
    