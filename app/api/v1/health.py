"""Health check API endpoints."""

from fastapi import APIRouter , Depends
from datetime import datetime

from app.models.schemas import HealthResponse
from app.config.settings import settings
from app.core.logging import get_logger
import time 
from app.services.ai_service import AIService
from app.api.dependencies import get_ai_service


logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check(ai_service: AIService = Depends(get_ai_service)):
    """
    Health check endpoint.
    
    Returns the current health status of the service.
    """
    start_time = time.perf_counter() # 1. Empezamos el cronómetro de alta precisión

    await ai_service.client.get("https://openrouter.ai/api/v1/models")

    end_time = time.perf_counter() # 2. Terminamos el cronómetro
    latency = end_time -start_time # 3. calculamos la diferencia
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.app_version,
        message=f"Service is running normally. Latency: {latency:.4f}s" # 4. Lo mostramos en el mensaje
    )
