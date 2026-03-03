"""
Servicio central de Inteligencia Artificial.
Gestiona la lógica de comunicación con OpenROuter, el procesamiento de 
prompts y la persistencia de datos en Supabase.
"""

import httpx
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.config.settings import settings
from app.models.schemas import ( 
    DatosClinicos,
    ResumenesPaciente, 
    RequestsPaciente , 
    ResumeniaRequest, 
    ResumeniaResponse, 
    ModelInfo,
    Vacunas
)
from app.core.logging import get_logger
from app.core.security import mask_api_key
from dateutil.relativedelta import relativedelta
import os

def cargar_prompt(nombre_archivo="system_prompt_llama_v3.txt"):
    """
    Carga las instrucciones del sistema desde un archivo de texto.
    Esto permite modificar el comportamiento de la IA sin tocar el código Python.
    """

    # 1. Definición de la ruta: Se busca en la carptea core/prompts.
    # Usar archivos externos permite ajustar el "tono" de la IA sin redeployar código.
    ruta = f"app/core/prompts/{nombre_archivo}"
    
    try:
        # 2. Intento de lectura: Abrimos el archivo con encoding utf-8 para evitar
        # problemas con tildes o caracteres especiales del español.
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read().strip()
    
    except FileNotFoundError:
        # 3. Fallback de seguridad: Si por error se borra el archivo o la ruta está mal escrita
        # devolvemos un prompt básico para qeu el servicio siga opetando y no devuelva error 500
        logger.warning(f"Archivo de prompt no encotnrado en: {ruta}. Usando configuración por defecto.")
        return "Sos un asistente veterinario. Tu tarea es resumir historiales clínicos en JSON."
    
    except Exception as e:
        # 4- Gestión de errores inseperados: Errores de permisos o lectura de disco. 
        print(f" Error inesperado al cargar el prompt: {e}")
        return "Error interno al cargar instrucciones."

CORE_GROUPS = {
    "CORE_MULTIPLE": {
        "vigencia_meses": 12,
        "keywords": [
            "sextuple", "séxtuple",
            "quintuple", "quíntuple",
            "dhpp", "dhppi",
            "vanguard",
            "nobivac",
            "biocan",
            "moquillo",
            "parvovirus",
            "adenovirus",
            "leptospira"
        ]
    },
    "RABIA": {
        "vigencia_meses": 12,
        "keywords": [
            "rabia",
            "antirrabica",
            "antirrábica",
            "defensor",
            "rabisin"
        ]
    }
}

import unicodedata

def normalizar_texto(texto: str) -> str:
    """
    Limpia y estandariza strings para comparaciones precisas.
    Remueve tildes, convierte a minusculas y elimina caracteres especiales.
    """
    # 1. LLevamos todo a minuscula
    texto = texto.lower()
    
    # 2. Descomponemos caracteres (ej: 'é' -> 'e' ->'´')
    texto = unicodedata.normalize("NFD", texto)

    # 3. Eliminamos tildes. Aseguramos que la busqueda no falle por un acento mal puesto
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto

def clasificar_vacuna(vacuna: Vacunas) -> str:
    """
    Asigna un grupo sanitario (CORE o RABIA) basandose en el nombre de la vacuna.
    Utiliza busqueda por palabras calve en los campos de tipo y nombre cientifico.

    """
    
    # 1. Preparación del input: Combinamos ambos campos para maximizar la probabilidad de match.
    # Si los campos vienen como None, usamos un string vacío para evitar errores de concatenación.
    texto = normalizar_texto(
        (vacuna.tipo or "") + " " +
        (vacuna.nombre_cientifico or "")
    )

    # 2. Match de Keywords: Iteramos el diccionario CORE_GROUPS buscando coincidencias.
    # Se prioriza el primer grupo encontrado según el orden definido en el diccionario.
    for grupo, data in CORE_GROUPS.items():
        for keyword in data["keywords"]:
            if keyword in texto:
                return grupo

# 3. Si no hay coincidencias, devolvemos un estado neutro para no sesgar a la IA.
    return "DESCONOCIDA"

def evaluar_vacunas(vacunas: list[Vacunas], fecha_actual: str):
    """
    Calcula la vigencia de cada vacuna y determina riesgos legales o sanitarios.
    Procesa las fechas en Python para entregar datos estructurados y precisos a la IA.
    """
    historial = []
    esquema_incompleto = False
    riesgo_legal = False

    try:
        # 1. Validación de Fecha Actual: Convertimos el string ISO del sistema a objeto datetime.
        # Este paso es crítico para poder realizar comparaciones matemáticas de tiempo.
        fecha_actual_dt = datetime.strptime(fecha_actual, "%Y-%m-%d")
        
        for vacuna in vacunas:
            try:
                # 2. Procesamiento Individual: Intentamos parsear la fecha de aplicación de cada vacuna.
                # Si el dato es un placeholder ("string", "asdf"), el bloque except interno lo captura.
                fecha_aplicacion = datetime.strptime(vacuna.fecha_aplicacion, "%Y-%m-%d")
                grupo = clasificar_vacuna(vacuna)


                if grupo != "DESCONOCIDA":
                # 3. Cálculo de Vencimiento: Se suma la vigencia en meses definida en la configuración.
                # El uso de relativedelta asegura un cálculo exacto de meses calendario.
                    meses = CORE_GROUPS.get(grupo, {}).get("vigencia_meses", 12)
                else:
                    meses = 12
                
                fecha_vencimiento = fecha_aplicacion + relativedelta(months=meses)

                # 4. Lógica de Flags: Comparamos contra la fecha de referencia para detectar vencimientos.
                if fecha_actual_dt > fecha_vencimiento:
                    estado = "VENCIDA"
                    esquema_incompleto = True
                    # Alerta Crítica: La rabia vencida implica un riesgo legal para el propietario.
                    if grupo == "RABIA":
                        riesgo_legal = True
                else:
                    estado = "AL_DIA"
                
                # 5. Estructuración: Creamos un diccionario limpio que la IA pueda interpretar fácilmente.
                historial.append({
                    "nombre": vacuna.tipo,
                    "grupo_sanitario": grupo,
                    "fecha_aplicacion": vacuna.fecha_aplicacion,
                    "estado": estado
                })
            except (ValueError, TypeError, KeyError):
                # Si una vacuna individual tiene basura, la ignoramos y seguimos
                continue

    except (ValueError, TypeError):
        # Si la fecha_actual es inválida, devolvemos el esquema base vacío
        print("Aviso: Error de formato en pre-procesamiento. Delegando validación a la IA.")
    
    return {
        "historial_vacunas": historial,
        "esquema_incompleto": esquema_incompleto,
        "riesgo_legal": riesgo_legal
    }
logger = get_logger(__name__)


class AIService:
    """
    Sercivio para imteractuar con la API de OpenROuter y gestionar 
    el ciclo de vida de los informes de IA.
    """
    
    def __init__(self):
        """
        inicializa el cliente HTTP asíncronico con la configuracion de OpenRouter.
        Se utiliza httpx para manejar petiiones no bloqueantes de forma eficiente.
        """
        # Configruación del cliente con headers obligatorios de OpenRouter
        self.client = httpx.AsyncClient(
            base_url=settings.nvidia_api_url,
            headers={
                "Authorization": f"Bearer {settings.nvidia_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-username/template-python-fastapi",
                "X-Title": settings.app_name,
            },
            timeout=140.0 # Tiempo de espera extendido para procesamiento de LLMs
        )
        # Log de confirmación con enmascaramiento de credenciales por seguridad
        logger.info(f"AI Service initialized with API key: {mask_api_key(settings.nvidia_api_key)}")  
    
    async def list_models(self) -> List[ModelInfo]:
        """List available models from OpenRouter."""
        try:
            logger.info("Fetching available models from NVIDIA NMI")
            response = await self.client.get("/models")
            response.raise_for_status()
            
            data = response.json()
            models_data = data.get("data", [])
            
            models = [
                ModelInfo(
                    id=model.get("id", ""),
                    name=model.get("name"),
                    description=model.get("description"),
                    pricing=model.get("pricing")
                )
                for model in models_data
            ]
            
            logger.info(f"Retrieved {len(models)} models")
            return models
            
        except httpx.HTTPStatusError as e:
            error_msg = f"NVIDIA NMI API error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error fetching models: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def health_check(self) -> bool:
        """Check if the AI service is healthy."""
        try:
            # Try to fetch models as a simple health check
            await self.list_models()
            return True
        except Exception as e:
            logger.error(f"AI service health check failed: {str(e)}")
            return False
    
    async def generar_resumenia(self, 
                                request: ResumeniaRequest ,
                                id_request_ia: int,
                                fecha_actual: str
                                ) -> ResumeniaResponse :
        """Cordina la generación del resumen médico con IA y su persistencia
        en la base de datos."""
        
        fecha_referencia = datetime.fromisoformat(fecha_actual).strftime("%Y-%m-%d")
        
        datos_modelo = request.datos_clinicos
        
        resultado_sanitario = evaluar_vacunas(
            datos_modelo.vacunas,
            fecha_referencia
        )
        
        datos = datos_modelo.model_dump()
        datos["evaluacion_sanitaria"] = resultado_sanitario
        datos["fecha_actual"] = fecha_referencia
        
        # 1. Prompt Engineering: Cargamos instruccions externas y armamos el historial
        system_prompt = cargar_prompt()
        messages = [
            {
                "role": "system", 
                "content": f"{system_prompt}<|eot|>"
            },
            {
                "role": "user", 
                "content": (
                    "DATOS DEL PACIENTE:\n"
                    f"```json\n{datos}\n```\n"
                    "Transforma estos datos en un resumen narrativo fluido, profesional y humano.<|eot|>"
                )
            }
        ]   

        # 2. Preparacion del Payload siguiendo el contrato de OpenRoute/Gemini
        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream,
        }

        print(f"DEBUG 1 - Fecha recibida: {fecha_actual} (Tipo: {type(fecha_actual)})")

        try:
            # 3. LLamada a la API externa
            logger.info(f"Enviando solicitud de completado a modelo: {request.model}")
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status() # lanza excepción si el status no es 2xx
            
            data = response.json()
            
            # 4. Validación de respuesta: Verificamos que la IA haya devuelto texto
            if "choices" not in data or not data["choices"]:
                raise ValueError("AI_RESPONSE_INVALID")
            content = data["choices"][0]["message"]["content"]

            # 5. Limpieza del contenido: quitamos posibles bloques de código Markdown
            content_clean = content.replace("```json", "").replace("```", "").strip()
            
            # 6. Carga del JSON generado por la IA
            print(f"--- CONTENIDO RECIBIDO ---\n{content_clean}\n--- FIN ---")
            ia_output = json.loads(content_clean)
            
            # 7. Lógica de limpieza: Si el input fue inválido, eliminamos el registro de auditoria
            if isinstance(ia_output, dict) and ia_output.get("error") == "INPUT_INVALIDO":
                    logger.warning(f"Inteto de resumen invalido para paciente {request.id_paciente}")
                    self.eliminar_registro(id_request_ia)
                    raise ValueError("AI_INPUT_INVALID")
            
            # 8. Extracción de campos obligatorios según el Schema
            resumen_completo = ia_output["resumen_completo"]
            resumen_estructurado = ia_output["resumen_estructurado"]

            # 9. Persistencia del Output: Guardamos el análisis final en la DB
            db_response = supabase.table("resumen_ia").insert({
                "id_paciente" : request.id_paciente,
                "id_request_ia": id_request_ia,
                "modelo": request.model,
                "resumen_completo": resumen_completo,
                "resumen_estructurado": resumen_estructurado,
            }).execute()

            # 10. Mapeo: Retornamos el primer objeto del inssert para el esquema de respuesta
            registro = db_response.data[0]
            return {
                    "id_resumenia": registro["id_resumenia"],
                    "id_paciente": registro["id_paciente"],
                    "modelo": registro["modelo"],
                    "resumen_completo": registro["resumen_completo"],
                    "resumen_estructurado": registro["resumen_estructurado"],
                    "fecha_generacion": registro["fecha_generacion"]
                    }
        
        # -------------------------------------------------------------------------------------------------
        # SECCION MANEJO DE EXCEPCIONES
        # -------------------------------------------------------------------------------------------------
        
        except httpx.TimeoutException:
            logger.error("Timeout en OpenRouter")
            raise ValueError("AI_TIMEOUT")
        except httpx.HTTPStatusError as e:
            # Mapeo de errores HTTP a errores de negocio internos
            status_code = e.response.status_code
            logger.error(f"Error {status_code} de Nvidia: {e.response.text}")
            if status_code == 401:
                raise ValueError("AI_AUTH_ERROR")
            elif status_code == 422:
                raise ValueError("AI_VALIDATION_ERROR") 
            else:
                raise ValueError("AI_PROVIDER_ERROR")
        except ValueError:
            # RELANZAMIENTO: Permite que errores de negocio (INPUT_INVALIDO) lleguen al Router
            raise
        except Exception as e:
            # Fallback crítico; logueamos el error y limpiamos el request huérfano
            logger.error(f"Error inesperado: {str(e)}")
            self.eliminar_registro(id_request_ia)
            raise ValueError("AI_UNKNOWN_ERROR")
    
    import hashlib
    def generar_hash(self, id_paciente: int ,datos : DatosClinicos ):
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
            return self.hashlib.sha256(carga_string.encode()).hexdigest()
        except Exception as e:
            print(f"Error al hashear el registro: {str(e)}")
    
    
    async def save_request(self,id_paciente: int, datos_clinicos: DatosClinicos):
        """
        Registra el input original en 'ia_request'.
        Fundamental para trazavilidad y re-entrenamiento del modelo.
        """
        # 1. Generamos el hash del registro.
        hash_request = self.generar_hash(id_paciente,datos_clinicos)        

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
    
    def total_request_paciente(self, id_paciente: int) -> RequestsPaciente:
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

    def total_resumenes_ia(self):
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

    def total_resumenes_ia_paciente(self, id_paciente: int) -> ResumenesPaciente:
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

    def total_requests(self):
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

    def eliminar_registro(self, id_registro : int):
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

    def registrar_metricas_db(self, resultado: str, segundos: float , error: str = None):
        try:
            supabase.table("metricas_ia").insert({
                "resultado": resultado,
                "duracion": segundos,
                "mensaje_error" : error
            }).execute()
    
        except Exception as e:
            logger.error(f"no se pudo guardar la métrica: {e}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("AI service client closed")


# Global AI service instance
ai_service = AIService()
