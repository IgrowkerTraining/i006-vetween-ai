"""AI service for OpenRouter integration."""

import httpx
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.config.settings import settings
from app.models.schemas import DatosClinicos,ResumenesPaciente, RequestsPaciente , ResumeniaRequest, ResumeniaResponse, ModelInfo
from app.core.logging import get_logger
from app.core.security import mask_api_key

import os

def cargar_prompt(nombre_archivo="system_prompt.txt"):
    # Ruta directa desde donde "estás parado" en la terminal
    ruta = f"app/core/prompts/{nombre_archivo}"
    
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Error: No encontré el archivo. Revisa si estás en la raíz del proyecto."

    except FileNotFoundError:
        print(f" Error: No se encontró el archivo de prompt en: {ruta}")
        # Retornamos un prompt mínimo de emergencia para que la App no deje de funcionar
        return "Sos un asistente veterinario. Tu tarea es resumir historiales clínicos en JSON."
    
    except Exception as e:
        print(f" Error inesperado al cargar el prompt: {e}")
        return "Error interno al cargar instrucciones."

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
    
    # Funcion para generar resumenes IA
    async def generar_resumenia(self, request: ResumeniaRequest ,id_request_ia: int) -> ResumeniaResponse :
        """Create a chat completion using OpenRouter API."""

        system_prompt = cargar_prompt()
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
    
    # Funcion para procesar datos de entrada y persistirse en DB
    async def save_request(id_paciente: int, datos_clinicos: DatosClinicos):
        response = supabase.table("ia_request").insert({
            "id_paciente": id_paciente,
            "datos_clinicos": datos_clinicos.model_dump()
        }).execute()
        return response.data[0]
    
    # Funcion obtener todos los requests de un paciente
    def total_request_paciente(self, id_paciente: int) -> RequestsPaciente:
        try:
            if not id_paciente:
                return None
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

    # Función para obtener todos los resumenes de la base de datos IA
    def total_resumenes_ia(self):
        try:
            response = (
                supabase
                .table("resumen_ia")
                .select("*")
                .order("fecha_generacion", desc= True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error obteniendo resumenes IA: {str(e)}")
            raise ValueError("DB_ERROR")

    # Función para obtener todos los resumenes IA de un paciente
    def total_resumenes_ia_paciente(self, id_paciente: int) -> ResumenesPaciente:
        try:
            if not id_paciente:
                return None
            response = (
                supabase
                .table("resumen_ia")
                .select("*")
                .eq("id_paciente", id_paciente)
                .order("fecha_generacion", desc= True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error obteniendo resumenes IA: {str(e)}")
            raise ValueError("DB_ERROR")

    # Función obtener todos los requests de la base de datos IA
    def total_requests(self):
        try:
            response = (
                supabase
                .table("ia_request")
                .select("*")
                .order("fecha_request", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error obteniendo resumenes IA: {str(e)}")
            raise ValueError("DB_ERROR") 
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("AI service client closed")


# Global AI service instance
ai_service = AIService()
