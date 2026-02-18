"""Chat-related API endpoints."""

from fastapi import APIRouter, HTTPException, Depends,status
from typing import List

from app.models.schemas import ModeloRequest, ResumeniaRequest, ResumeniaResponse, ModelInfo
from app.services.ai_service import AIService
from app.api.dependencies import get_ai_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/completions", response_model=ResumeniaResponse)
async def create_chat_completion(
    request: ResumeniaRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Create a chat completion using OpenRouter API.
    
    - **model**: AI model to use (e.g., "openai/gpt-3.5-turbo")
    - **messages**: List of chat messages
    - **max_tokens**: Maximum tokens to generate (1-4096)
    - **temperature**: Sampling temperature (0.0-2.0)
    - **stream**: Enable streaming response (not yet implemented)
    """
    try:
        logger.info(f"Chat completion request for model: {request.model}")
        response = await ai_service.chat_completion(request)
        return response
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=List[ModelInfo])
async def list_models(ai_service: AIService = Depends(get_ai_service)):
    """
    List all available AI models from OpenRouter.
    
    Returns a list of available models with their information.
    """
    try:
        models = await ai_service.list_models()
        return models
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Creación de endpoint provisoria para probar persistencia en DB
@router.post("/request", response_model=dict)
async def guardar_datosDB(request: ResumeniaRequest):
    try:
        guardar_request = await AIService.save_request(
            request.id_paciente,
            request.datos_clinicos
        )

        return {
            "mensaje": "guardado correcto en base de datos",
        
            "status": "Creado"
            }
    except Exception as e:
        logger.error(f"Error al cargar datos: {str(e)}")
        raise HTTPException( detail=str(e))

# Endpoint Response IA
@router.post("/resumenia", response_model=ResumeniaResponse)
async def chat(request: ResumeniaRequest, ai_service: AIService = Depends(get_ai_service)):
    try:
        logger.info(f"Resumen request for model: {request.model}")
        guardar_request = await AIService.save_request(
            request.id_paciente,
            request.datos_clinicos
        )
        
        data = await ai_service.chat(request)
        return data
    # Manejo de errores al comunicarse con IA
    except ValueError as e:
        error_msg = str(e)
        
        if error_msg == "AI_TIMEOUT":
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT, 
                detail="La IA está tardando demasiado. Por favor, intenta de nuevo."
            )
        elif error_msg == "AI_AUTH_ERROR":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Error de configuración interna (Auth)."
            )
        elif error_msg == "AI_VALIDATION_ERROR":
            raise HTTPException(status_code=500, detail="La IA rechazo los datos por formato invalido.")
        
        elif error_msg == "AI_PROVIDER_ERROR":
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, 
                detail="El servicio de IA no está disponible en este momento."
            )
        # Manejo de validacion de salida
        elif error_msg == "AI_RESPONSE_INVALID":
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, 
                detail="La IA respondió correctamente pero el formato del resumen no es válido."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Ocurrió un error inesperado al procesar la IA."
            )

# Endpoint Obtener los requests de un paciente
@router.get("/request/{id_paciente}", response_model=list[ModeloRequest])
async def requests_paciente(
    id_paciente : int , 
    ai_service : AIService = Depends(get_ai_service)):
    try:
        data = await ai_service.total_request_paciente(id_paciente)
        return data
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo los requests del paciente"
        )
