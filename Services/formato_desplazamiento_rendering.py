from pathlib import Path
import math
import os
import tempfile
from django.http import HttpResponse
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
        'es_corporacion': tipo_esquema.get('es_corporacion', False),
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
    Extrae pasajeros que tengan vuelos (aereo=True)'''
    datos_pasajeros = []
    
    # Add passengers who have vuelos (flights)
    for servicio in servicios:
        if servicio.get('Requerimientos', {}).get('aereo', False) and servicio.get('vuelos'):
            pasajero = {
                'nombres': servicio.get('nombre_pdp', ''),
                'apellidos': servicio.get('apellido_pdp', ''),
                'cedula': servicio.get('cedula_pdp', ''),
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
    '''Mapea los vuelos IDA y REGRESO desde TODOS los servicios (sin duplicados)
    Args:
        servicios: lista completa de servicios
    Returns:
        dict: diccionario con solo ida y regreso
    '''
    # Estructura base para ida y regreso
    resultado = {
        'ida': {
            'fecha': '',
            'hora': '',
            'origen': '',
            'destino': '',
            'aerolinea': '',
            'vuelo': '',
            'tipo': 'Ida'
        },
        'regreso': {
            'fecha': '',
            'hora': '',
            'origen': '',
            'destino': '',
            'aerolinea': '',
            'vuelo': '',
            'tipo': 'Regreso'
        }
    }
    
    # Buscar y asignar IDA y REGRESO de los servicios
    for servicio in servicios:
        vuelos = servicio.get('vuelos', [])
        for vuelo in vuelos:
            tipo = vuelo.get('tipo', '')
            if tipo == 'Ida' and not resultado['ida']['vuelo']:
                resultado['ida'] = {
                    'fecha': vuelo.get('fecha_vuelo', ''),
                    'hora': vuelo.get('hora_vuelo', ''),
                    'origen': vuelo.get('origen', ''),
                    'destino': vuelo.get('destino', ''),
                    'aerolinea': vuelo.get('aerolinea', ''),
                    'vuelo': vuelo.get('numero_vuelo', ''),
                    'tipo': 'Ida'
                }
            elif tipo == 'Regreso' and not resultado['regreso']['vuelo']:
                resultado['regreso'] = {
                    'fecha': vuelo.get('fecha_vuelo', ''),
                    'hora': vuelo.get('hora_vuelo', ''),
                    'origen': vuelo.get('origen', ''),
                    'destino': vuelo.get('destino', ''),
                    'aerolinea': vuelo.get('aerolinea', ''),
                    'vuelo': vuelo.get('numero_vuelo', ''),
                    'tipo': 'Regreso'
                }
    
    return resultado


def mapear_datos_conexiones(servicios:list):
    '''Mapea solo las CONEXIONES desde los servicios de una página específica
    Args:
        servicios: lista de servicios de la página actual
    Returns:
        list: lista con hasta 2 conexiones
    '''
    # Recopilar vuelos de tipo CONEXIÓN de esta página
    conexiones_data = []
    for servicio in servicios:
        vuelos = servicio.get('vuelos', [])
        for vuelo in vuelos:
            if vuelo.get('tipo') == 'Conexion':
                conexion = {
                    'fecha': vuelo.get('fecha_vuelo', ''),
                    'hora': vuelo.get('hora_vuelo', ''),
                    'origen': vuelo.get('origen', ''),
                    'destino': vuelo.get('destino', ''),
                    'aerolinea': vuelo.get('aerolinea', ''),
                    'vuelo': vuelo.get('numero_vuelo', ''),
                    'tipo': 'Conexion'
                }
                conexiones_data.append(conexion)
    
    # Estructura base para conexiones (siempre 2 slots)
    conexiones = [
        {
            'fecha': '',
            'hora': '',
            'origen': '',
            'destino': '',
            'aerolinea': '',
            'vuelo': '',
            'tipo': 'Conexion'
        },
        {
            'fecha': '',
            'hora': '',
            'origen': '',
            'destino': '',
            'aerolinea': '',
            'vuelo': '',
            'tipo': 'Conexion'
        }
    ]
    
    # Asignar vuelos como conexiones (hasta 2)
    for i, conexion_data in enumerate(conexiones_data):
        if i < 2:
            conexiones[i] = conexion_data
    
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
    template_path = base_path / 'Assets' / 'Formato_desplazamiento_fillable.pdf'
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
    
    campos['Ciudad'] = context['origen_destino']['ciudad_origen']
    campos['Fecha'] = context['fechas']['fecha_inicio']

    campos['Esquema_extensivo_Si'] = 'X' if context['tipo_esquema']['extensivo_nucleo_familiar'] else ''
    campos['Esquema_extensivo_No'] = '' if context['tipo_esquema']['extensivo_nucleo_familiar'] else 'X'

    # Tipo de esquema (checkboxes)
    campos['Corporacion'] = 'X' if context['tipo_esquema']['es_corporacion'] else ''
    campos['Colectivo'] = 'X' if context['tipo_esquema']['es_colectivo'] else ''
    campos['Individual'] = 'X' if context['tipo_esquema']['es_individual'] else ''
    
    # Datos del esquema
    esquema = context['datos_esquema']
    campos['Nombre corp'] = esquema['nombre_corp']
    campos['NIT corp'] = esquema['nit_corp']
    campos['Celular corp'] = esquema['celular_corp']
    campos['Poblacion CERREM'] = esquema['poblacion_cerrem']
    campos['Nombre rep'] = esquema['nombre_rep']
    campos['Cedula rep'] = esquema['cedula_rep']
    campos['Celular rep'] = esquema['celular_rep']
    campos['Poblacion CERREM rep'] = esquema['poblacion_cerrem']
    campos['Nombre bnf'] = esquema['nombre_benef']
    campos['Cedula bnf'] = esquema['cedula_benef']
    campos['Celular bnf'] = esquema['celular_benef']
    campos['Poblacion CERREM'] = esquema['poblacion_cerrem']
    
    # Requerimientos generales
    req = context['requerimientos_generales']
    campos['Terrestre'] = 'X' if req['terrestre'] else ''
    campos['Aereo'] = 'X' if req['aereo'] else ''
    campos['Fluvial'] = 'X' if req['fluvial'] else ''
    
    # Origen y destino
    origen_destino = context['origen_destino']
    campos['Ciudad_origen_CERREM'] = origen_destino['ciudad_origen']
    campos['Departamento_origen_CERREM'] = origen_destino['departamento_origen']
    campos['Ciudades_municipios_destino'] = origen_destino['ciudad_destino']
    campos['tipo_desplazamiento'] = origen_destino['tipo']
    
    # Fechas
    fechas = context['fechas']
    campos['Dia_inicio'] = str(fechas['inicio']['dia'])
    campos['Mes_inicio'] = str(fechas['inicio']['mes'])
    campos['Anio_inicio'] = str(fechas['inicio']['anio'])
    campos['Dia_fin'] = str(fechas['fin']['dia'])
    campos['Mes_fin'] = str(fechas['fin']['mes'])
    campos['Anio_fin'] = str(fechas['fin']['anio'])
    
    # PDPs (4 por página)
    for i, pdp in enumerate(context['pdps'], 1):
        campos[f'Nombre_pdp{i}'] = pdp['nombres_pdp']
        campos[f'Apellido_pdp{i}'] = pdp['apellidos_pdp']
        campos[f'Cedula_pdp{i}'] = pdp['cedula_pdp']
        campos[f'Telefono_pdp{i}'] = pdp['telefono_contacto']
        campos[f'Fija_pdp{i}'] = 'X' if pdp['nombres_pdp'] and pdp['fija'] else ''
        campos[f'Temporal_pdp{i}'] = 'X' if pdp['nombres_pdp'] and pdp['temporal'] else ''
    
    # Pasajeros (4 filas)
    for i, pasajero in enumerate(context['tiquetes']['pasajeros'], 1):
        campos[f'Nombre_pasajero{i}'] = pasajero['nombres']
        campos[f'Apellido_pasajero{i}'] = pasajero['apellidos']
        campos[f'Cedula_pasajero{i}'] = pasajero['cedula']
        campos[f'Telefono_pasajero{i}'] = pasajero['telefono_contacto']
    
    # Segmentos de vuelo (IDA, CONEXIÓN 1, CONEXIÓN 2, REGRESO)
    segmentos = context['tiquetes']['segmentos']

    # IDA
    campos['Fecha_ida'] = segmentos['ida']['fecha']
    campos['Hora_ida'] = segmentos['ida']['hora']
    campos['Origen_ida'] = segmentos['ida']['origen']
    campos['Destino_ida'] = segmentos['ida']['destino']
    campos['Aereolinea_ida'] = segmentos['ida']['aerolinea']
    campos['Vuelo_ida'] = segmentos['ida']['vuelo']
    
    for i, conexion in enumerate(segmentos['conexiones'], 1):
        campos[f'Fecha_conexion{i}'] = conexion['fecha']
        campos[f'Hora_conexion{i}'] = conexion['hora']
        campos[f'Origen_conexion{i}'] = conexion['origen']
        campos[f'Destino_conexion{i}'] = conexion['destino']
        campos[f'Aereolinea_conexion{i}'] = conexion['aerolinea']
        campos[f'Vuelo_conexion{i}'] = conexion['vuelo']
    
    # REGRESO
    campos['Fecha_regreso'] = segmentos['regreso']['fecha']
    campos['Hora_regreso'] = segmentos['regreso']['hora']
    campos['Origen_regreso'] = segmentos['regreso']['origen']
    campos['Destino_regreso'] = segmentos['regreso']['destino']
    campos['Aereolinea_regreso'] = segmentos['regreso']['aerolinea']
    campos['Vuelo_regreso'] = segmentos['regreso']['vuelo']
    

    return campos


#Función principal de renderizado del PDF
def unir_pdfs_temporales(rutas_pdfs:list):
    '''Une múltiples PDFs desde archivos temporales en un solo PDF
    Args:
        rutas_pdfs: lista de rutas a archivos PDF generados
    Returns:
        PdfWrapper: objeto PDF unido
    '''
    if not rutas_pdfs:
        raise ValueError("No hay PDFs para unir")
    
    # Cargar el primer PDF
    pdf_final = PdfWrapper(rutas_pdfs[0])
    
    # Unir los demás PDFs
    for ruta_pdf in rutas_pdfs[1:]:
        pdf_a_agregar = PdfWrapper(ruta_pdf)
        pdf_final = pdf_final + pdf_a_agregar
    
    return pdf_final


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
    
    # Lista para almacenar las rutas de los PDFs temporales generados
    rutas_pdfs_temporales = []
    
    try:
        # Generar un PDF por cada página necesaria
        for pagina in range(1, cantidad_formatos + 1):
            # Formatear el contexto para esta página
            context = formatear_contexto_por_pagina(desplazamiento, pagina, cantidad_formatos)
            
            # Mapear los datos a los campos del PDF
            campos = mapear_campos_pdf(context, pagina)
            
            # Cargar el template y llenar los campos
            pdf = PdfWrapper(template_path)
            pdf = pdf.fill(campos, flatten=True)
            
            # Guardar el PDF en un archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=None) as tmp_file:
                pdf.write(tmp_file.name)
                rutas_pdfs_temporales.append(tmp_file.name)
        
        # Unir los PDFs si hay múltiples
        if len(rutas_pdfs_temporales) > 1:
            pdf_final = unir_pdfs_temporales(rutas_pdfs_temporales)
        else:
            # Solo hay un PDF
            pdf_final = PdfWrapper(rutas_pdfs_temporales[0])
        
        # Crear el response HTTP con el PDF
        merged = pdf_final

        merged.write("Formato_desplazamiento_llenado.pdf")

        return merged
    
    finally:
        # Limpiar los archivos temporales
        for ruta in rutas_pdfs_temporales:
            try:
                if os.path.exists(ruta):
                    os.remove(ruta)
            except Exception as e:
                print(f"Error al eliminar archivo temporal {ruta}: {e}")