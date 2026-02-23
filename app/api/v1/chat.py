"""Chat-related API endpoints."""

from fastapi import APIRouter, HTTPException, Depends,status
from typing import List

from app.models.schemas import ModeloResumen ,ModeloRequest, ResumeniaRequest, ResumeniaResponse, ModelInfo
from app.services.ai_service import AIService
from app.api.dependencies import get_ai_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


        # ENDPOINT DE DIAGNOSTICO
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
    
    #   ENDPOINTS DE NEGOCIO 
# Endpoint Response IA
@router.post("/resumenia", response_model=ResumeniaResponse)
async def resumen_ia(request: ResumeniaRequest, ai_service: AIService = Depends(get_ai_service)):
    try:
        logger.info(f"Resumen request for model: {request.model}")
        guardar_request = await AIService.save_request(
            request.id_paciente,
            request.datos_clinicos
        )
        id_request = guardar_request["id_request_ia"]
        data = await ai_service.generar_resumenia(request,id_request)

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
        elif error_msg == "AI_INPUT_INVALID":
            raise HTTPException(
                status_code=422, 
                detail="El contenido proporcionado no es un caso clínico veterinario válido."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Ocurrió un error inesperado al procesar la IA."
            )


# Endpoint obtener todos los resumenes de la base de datos IA
@router.get("/resumenia", response_model=List[ModeloResumen])
def listar_todos_los_resumenes(ai_service: AIService = Depends(get_ai_service)):
    try:
        return ai_service.total_resumenes_ia()
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail="Error interno al obtener el listado de resumenes"
        )

# Endpoint Obtener los resumenes del paciente
@router.get("/resumenia/{id_paciente}", response_model=list[ModeloResumen])
def resumenes_paciente(
    id_paciente : int , 
    ai_service : AIService = Depends(get_ai_service)):
    try:
        data = ai_service.total_resumenes_ia_paciente(id_paciente)
        
        # Validar si la lista viene vacia
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron resumenes para el paciente con ID: {id_paciente}"
            )
        return data
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo los requests del paciente"
        )

# Endpoint provisoria para probar persistencia en DB
@router.get("/request", response_model=List[ModeloRequest])
def listar_requests(ai_service : AIService = Depends(get_ai_service)):
    try:
        return ai_service.total_requests()
    except Exception as e:
        logger.error(f"Error al cargar datos: {str(e)}")
        raise HTTPException( detail=str(e))
# Endpoint Obtener los requests de un paciente
@router.get("/request/{id_paciente}", response_model=list[ModeloRequest])
def requests_paciente(
    id_paciente : int , 
    ai_service : AIService = Depends(get_ai_service)):
    try:
        data = ai_service.total_request_paciente(id_paciente)
        
        # Validar si la lista viene vacia
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron request para el paciente con ID: {id_paciente}"
            )
        return data
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo los requests del paciente"
        )

