"""AI service for OpenRouter integration."""

import httpx
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.config.settings import settings
from app.models.schemas import RequestsPaciente , ResumeniaRequest, ResumeniaResponse, ModelInfo
from app.core.logging import get_logger
from app.core.security import mask_api_key

logger = get_logger(__name__)


class AIService:
    """Service for interacting with OpenRouter API."""
    
    def __init__(self):
        """Initialize the AI service."""
        self.client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url,
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-username/template-python-fastapi",
                "X-Title": settings.app_name,
            },
            timeout=60.0
        )
        logger.info(f"AI Service initialized with API key: {mask_api_key(settings.openrouter_api_key)}")  
    
        # Funcion para generar una respuesta simple de IA
    async def generar_resumenia(self, request: ResumeniaRequest ,id_request_ia: int) -> ResumeniaResponse :
        """Create a chat completion using OpenRouter API."""

        system_prompt = """
            Sos un asistente veterinario especializado en generar resúmenes clínicos profesionales.

            Tu tarea es generar DOS salidas:
            1) Un resumen clínico redactado en texto profesional.
            2) Un resumen estructurado en formato JSON.

            Reglas obligatorias:
            - Responder siempre en español.
            - No inventar información.
            - No agregar texto fuera del JSON.
            - La respuesta debe ser únicamente un JSON válido.

            Formato obligatorio:

            {
            "resumen_completo": "Texto completo del resumen clínico",
            "resumen_estructurado": {
                "estado_general": "",
                "tipo_paciente": "",
                "descripcion_clinica": "",
                "tratamiento_indicado": "",
                "factores_riesgo": [],
                "puntos_clave_proximas_consultas": []
                }
            }   
            """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generá un resumen estructuradocon estos datos: {request.datos_clinicos}"}
        ]
        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream,
        }

        try:
            logger.info(f"Sending chat completion request for model: {request.model}")
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificamos que existan las claves que esperamos (la "salida")
            if "choices" not in data or not data["choices"]:
                raise ValueError("AI_RESPONSE_INVALID")
            content = data["choices"][0]["message"]["content"]

            # 1. Limpieza básica: quitamos posibles bloques de código de markdown
            content_clean = content.replace("```json", "").replace("```", "").strip()
    
            # 2. Intentamos cargar el JSON
            print(f"--- CONTENIDO RECIBIDO ---\n{content}\n--- FIN ---")
            ia_output = json.loads(content_clean)
            #ia_output = json.loads(content)
            resumen_completo = ia_output["resumen_completo"]
            resumen_estructurado = ia_output["resumen_estructurado"]

            db_response = supabase.table("resumen_ia").insert({
                "id_paciente" : request.id_paciente,
                "id_request_ia": id_request_ia,
                "modelo": request.model,
                "resumen_completo": resumen_completo,
                "resumen_estructurado": resumen_estructurado,
            }).execute()

            registro = db_response.data[0]
            return {
                    "id_resumenia": registro["id_resumenia"],
                    "id_paciente": registro["id_paciente"],
                    "modelo": registro["modelo"],
                    "resumen_completo": registro["resumen_completo"],
                    "resumen_estructurado": registro["resumen_estructurado"],
                    "fecha_generacion": registro["fecha_generacion"]
                    }
        # Manejo manual de errores al comunicarse con IA  
        except httpx.TimeoutException:
            logger.error("Timeout en OpenRouter")
            raise ValueError("AI_TIMEOUT")

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            print("aca badgateway")
            logger.error(f"Error {status_code} de OpenRouter: {e.response.text}")
            
            if status_code == 401:
                raise ValueError("AI_AUTH_ERROR")
            elif status_code == 422:
                raise ValueError("AI_VALIDATION_ERROR") 
            else:
                raise ValueError("AI_PROVIDER_ERROR")

        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            raise ValueError("AI_UNKNOWN_ERROR")



    async def list_models(self) -> List[ModelInfo]:
        """List available models from OpenRouter."""
        try:
            logger.info("Fetching available models from OpenRouter")
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
            error_msg = f"OpenRouter API error: {e.response.status_code} - {e.response.text}"
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
    # Funcion provisoria para procesar datos de entrada y persistirse en DB
    async def save_request(id_paciente: int, datos_clinicos: dict):
        response = supabase.table("ia_request").insert({
            "id_paciente": id_paciente,
            "datos_clinicos": datos_clinicos
        }).execute()
        return response.data[0]
    
    # Funcion obtener todos los requests de un paciente
    async def total_request_paciente(self, id_paciente: int) -> RequestsPaciente:
        try:
            response =(
                supabase
                .table("ia_request")
                .select("*")
                .eq("id_paciente", id_paciente)
                .order("fecha_request",  desc = True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error obteniendo requests IA: {str(e)}")
            raise ValueError("DB_ERROR")


    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("AI service client closed")


# Global AI service instance
ai_service = AIService()
