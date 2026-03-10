"""
Servicio central de Inteligencia Artificial.
Gestiona la lógica de comunicación con OpenROuter, el procesamiento de 
prompts y la persistencia de datos en Supabase.
"""

import httpx
import json
import hashlib
from datetime import datetime
from typing import List
from app.core.database import supabase
from app.config.settings import settings
from app.models.schemas import ( 
    DatosClinicos, 
    ResumeniaRequest, 
    ResumeniaResponse, 
    ModelInfo,
)
from app.core.logging import get_logger
from app.core.security import mask_api_key
from app.services.gestion_vacunas import evaluar_vacunas
from app.core.prompt_manager import cargar_prompt

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
            "response_format": { "type": "json_object" }
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
                    logger.error(f"AI_INPUT_INVALID: {str(request)}")
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
            logger.error("Timeout en NVIDIA NMI")
            raise ValueError("AI_TIMEOUT")
        except httpx.HTTPStatusError as e:
            # Mapeo de errores HTTP a errores de negocio internos
            status_code = e.response.status_code
            logger.error(f"Error {status_code} de Nvidia: {e.response.text}")
            if status_code == 401:
                logger.error(f"AI_AUTH_ERROR: {str(e)}")
                raise ValueError("AI_AUTH_ERROR")
            elif status_code == 422:
                logger.error(f"AI_VALIDATION_ERROR: {str(e)}")
                raise ValueError("AI_VALIDATION_ERROR") 
            else:
                logger.error(f"AI_PROVIDER_ERROR: {str(e)}")
                raise ValueError("AI_PROVIDER_ERROR")
        except ValueError:
            # RELANZAMIENTO: Permite que errores de negocio (INPUT_INVALIDO) lleguen al Router
            raise
        except Exception as e:
            # Fallback crítico; logueamos el error y limpiamos el request huérfano
            logger.error(f"Error inesperado: {str(e)}")
            self.eliminar_registro(id_request_ia)
            raise ValueError("AI_UNKNOWN_ERROR")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("AI service client closed")


# Global AI service instance
ai_service = AIService()
