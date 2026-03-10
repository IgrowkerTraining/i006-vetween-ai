from app.core.database import supabase
from app.core.logging import get_logger
from app.models.schemas import DatosClinicos,RequestsPaciente,ResumenesPaciente
import json, hashlib

logger = get_logger(__name__)

def generar_hash(id_paciente: int ,datos : DatosClinicos ):
        """
        Genera el hash del input original
        """
        try:
            # 1. Guardamos en un diccionario todos los datos.
            registro = {
                "id_p": id_paciente,
                # Desacoplamos Pydantic para extraer los datos puros
                "datos_c": datos.model_dump()
            }
        
            # 2. Serializamos el JSON con las claves ordenadas
            carga_string = json.dumps(registro, sort_keys= True)
        
            # 3. Retornamos el hash del registro
            return hashlib.sha256(carga_string.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error al hashear el registro: {str(e)}")
            raise e

async def save_request(id_paciente: int, datos_clinicos: DatosClinicos):
        """
        Registra el input original en 'ia_request'.
        Fundamental para trazavilidad y re-entrenamiento del modelo.
        """
        # 1. Generamos el hash del registro.
        hash_request = generar_hash(id_paciente,datos_clinicos)        

        try:
            # 2. Persistimos la información en la DB.
            response = supabase.table("ia_request").insert({
                "id_paciente": id_paciente,
                "datos_clinicos": datos_clinicos.model_dump(),
                "hash": hash_request
            }).execute()
            return response.data[0]
        except Exception as e:
            logger.info(f"Error guardando datos en DB: {str(e)}")

def total_request_paciente(id_paciente: int) -> RequestsPaciente:
    """
    Recuperar el historial de peticiones (inputs) enviadas a la IA para un paciente.
    """
    try:
        # 1. Validación de entrada: Verificamos que el ID no sea nulo o cero.
        if not id_paciente:
            return None
            
        # 2. Consulta ala tabla de auditoria:
        # Filtramos por id_paciente y ordenamos cronológicamente (más reciente primero)
        response =(
            supabase
            .table("ia_request")
            .select("*")
            .eq("id_paciente", id_paciente)
            .order("fecha_request",  desc = True)
            .execute()
        )

        # 3. Retorno de datos: Devolvemos la lista de registros encontrados.
        return response.data
        
    except Exception as e:
        # 4. Registro de errores: Si falla la conexión con Supabase o la consulta,
        # logueamos el detalle técnico y lanzamos un error de negocio.
        logger.error(f"Error obteniendo requests IA: {str(e)}")
        raise ValueError("DB_ERROR")

def total_resumenes_ia():
        """
        Recupera el listado completo de todos los informes generados por la IA.
        Se utiliza principalmente para visitas administrativas o auditoria general.
        """
        try:
            # 1. Consulta global a Supabase: Traemos todos los registros de la tabla 'resumen_ia'.
            # aplicamos un orden descendente por fecha para mostrar siempre la más nueva primero.
            response = (
                supabase
                .table("resumen_ia")
                .select("*")
                .order("fecha_generacion", desc= True)
                .execute()
            )

            # 2. Retorno de la data: FastAPI se encargará de convertir esta lista en el JSON de respuesta.
            return response.data

        except Exception as e:
            # 3. Gestión de errores de infraestructura: Logueamos el error real para el desarrollador
            # y lanzamos un ValueError genérico para que el Router lo transforme en un HTTP 500
            logger.error(f"Error obteniendo resumenes IA: {str(e)}")
            raise ValueError("DB_ERROR")
        

def total_resumenes_ia_paciente(id_paciente: int) -> ResumenesPaciente:
        """
        Consulta el historial de informes/resúmenes generados por la IA
        específicamente para un paciente.
        """
        try:
            # 1. Validación de seguridad: Evitamos consultas si no hay un ID de paciente.
            if not id_paciente:
                return None
            
            # 2. Consulta filtrada en Supabase:
            # Buscamos en la tabla 'resumen_ia' donde el ID coincida.
            # Ordenamos por 'fecha_generacion' DESC para que el último análisis esté arriba.
            response = (
                supabase
                .table("resumen_ia")
                .select("*")
                .eq("id_paciente", id_paciente)
                .order("fecha_generacion", desc= True)
                .execute()
            )

            # 3. Retorno de la información: Devolvemos los datos para ser mostrados en el historial.
            return response.data
        
        except Exception as e:
            # 4. Control de errores: Registramos el fallo técnico para debugging
            # y notificamos un error de base de datos a la capa superior.
            logger.error(f"Error obteniendo resumenes IA: {str(e)}")
            raise ValueError("DB_ERROR")

def total_requests():
        """
        Recupera el historial global de todas las peticiones enviadas a la IA.
        Sirve para auditoria general y monitoreo del volumen de uso del sistema.
        """
        try:
            # 1. Consulta a Supabase: Seleccionamos todos los campos de la tabla 'ia_request'.
            # Usamos el orden descendente por 'fecha_request' para que el administrador
            # vea siempre los últimos eventos en la parte superior.
            response = (
                supabase
                .table("ia_request")
                .select("*")
                .order("fecha_request", desc=True)
                .execute()
            )

            # 2. Retorno de datos: Devolvemos la lista de diccionarios con el input original.
            return response.data
        
        except Exception as e:
            # 3. Gestión de errores: Logueamos el error técnico para debugging.
            # Lanazamos VAlueErrror para que la capa supuerior sepa que hubo un fallo de DB.
            logger.error(f"Error obteniendo resumenes IA: {str(e)}")
            raise ValueError("DB_ERROR") 

def eliminar_registro( id_registro : int):
        """
        Elimina un registro de auditoria de la 'ia_request'.
        Se utiliza para limpieza autómatica cuando la generación de la IA falla
        o cuando el input detectado es inválido.
        """
        try:
            # 1. Log de operación: Registramos el intento de eliminación para trazabilidad
            logger.info(f"Eliminando registro de auditoria invalido: {id_registro}")
            
            # 2. Operación de borrado en Supabase:
            # Filtramos por la clave primaria 'id_request_ia' para asegurar un borrado preciso.
            response = (
                supabase
                .table("ia_request")
                .delete()
                .eq("id_request_ia",id_registro)
                .execute()
            )

            # 3. Retrono de confirmación: Devolvemos la respuesta de la DB.
            return response
        
        except Exception as e:
            # 4. Manejo de errorres: Si falla la conexión, logueamos el error pero no
            # lanzamos excepción hacia arriba para no interrumpir el flujo principal.
            logger.error(f"Error al intentar eliminar el registro {id_registro}: {str(e)}")
            raise ValueError("DB_ERROR")

def registrar_metricas_db(resultado: str, segundos: float , error: str = None):
        """
        Registra las metricas de rendimiento y auditoria del servicio IA.
        Se persisten latencia, tipo de respuesta (CACHE_HIT/CACHE_MISS/FALLO) y detalles de error
        """
        try:
            # 1. Persistimos los datos en la tabla "metricas_ia" en la DB.
            supabase.table("metricas_ia").insert({
                "resultado": resultado,
                "duracion": segundos,
                "mensaje_error" : error
            }).execute()
    
        except Exception as e:
            # 2. Logueamos el error si falla la persistencia.
            logger.error(f"no se pudo guardar la métrica: {e}")