"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field ,ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class ResumeniaRequest(BaseModel):
    """Chat completion request model."""
    model: str = Field(default="google/gemini-2.0-flash-001", description="AI model to use")
    #messages: List[ChatMessage] = Field(..., description="List of chat messages")
    
    # Agrego las validaciones de las entradas para los campos de la DB
    id_paciente: int = Field(... , description="ID del paciente")
    datos_clinicos: Dict[str, Any] = Field(... , description="Historial clinico")

    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=2.0, description="Sampling temperature")
    stream: Optional[bool] = Field(default=False, description="Enable streaming response")

class Vacuna(BaseModel):
    nombre: str
    fecha_aplicacion: str
    estado: str

class Visita(BaseModel):
    fecha: str
    motivo: str
    diagnostico: str
    tratamiento: str

class ResumenEstructurado(BaseModel):
    estado_general: str
    tipo_paciente: str
    sintesis_visitas: List[Visita]
    historial_vacunas: List[Vacuna]
    descripcion_clinica: str
    tratamiento_indicado: str
    factores_riesgo: List[str]
    puntos_clave_proximas_consultas: List[str]

class ResumeniaResponse(BaseModel):
    """Chat completion response model."""
    # modifico y agrego los campos a validar segun la tabla de la DB y
    id_resumenia: str = Field(..., description="Resumen ID")
    id_paciente: int = Field(..., description="ID del paciente")
    resumen_completo : str = Field(..., description="Resumen en texto plano")
    resumen_estructurado: ResumenEstructurado = Field(..., description="Resumen JSON estructudado")
    modelo: str = Field(..., description="Model used")
    fecha_generacion: datetime = Field(default_factory=datetime.now, description="Fecha de creacion del resumen")
    #object: str = Field(default="chat.completion", description="Object type")
    
    #choices: List[Dict[str, Any]] = Field(..., description="Response choices")
    usage: Optional[Dict[str, int]] = Field(default=None, description="Token usage information")
    model_config = ConfigDict(from_attributes=True)

class ModelInfo(BaseModel):
    """AI model information."""
    id: str = Field(..., description="Model ID")
    name: Optional[str] = Field(default=None, description="Model display name")
    description: Optional[str] = Field(default=None, description="Model description")
    pricing: Optional[Dict[str, Any]] = Field(default=None, description="Pricing information")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field(..., description="Application version")
    message: Optional[str] = Field(default=None, description="Additional status message")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    detail: Optional[str] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class RootResponse(BaseModel):
    """Root endpoint response model."""
    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="Application version")
    docs: str = Field(..., description="Documentation URL")
    health: str = Field(..., description="Health check URL")


# Schema y subSchema para validar la obtencion de los requests del pacientes
class ModeloRequest(BaseModel):
    id_request_ia : str = Field(..., description="ID del request")
    id_paciente : int = Field(..., description="ID del paciente")
    datos_clinicos : Dict[str, Any] = Field(..., description="Historia clinica del paciente")
    fecha_request: datetime = Field(..., description="Fecha del request" )


class RequestsPaciente(BaseModel):
    data: List[ModeloRequest] 

# Schemas para validar la obtención de resumenes IA por paciente
class ModeloResumen(BaseModel):
    id_resumenia: str = Field(..., description="ID resumen IA")
    id_paciente : int = Field(..., description="ID del paciente")
    resumen_completo: str = Field(..., description="Texto completo del resumen")
    resumen_estructurado: Dict[str, Any] = Field(..., description="Resumen IA estructurado")
    fecha_generacion: datetime = Field(...,description= "Fecha de generacion del resumen IA") 

class ResumenesPaciente(BaseModel):
    data: List[ModeloResumen]