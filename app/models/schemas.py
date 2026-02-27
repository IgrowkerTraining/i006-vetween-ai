"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field ,ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")

# --- Modelos del Dominio Veterinario ---

class Paciente(BaseModel):
    """Información base de la mascota."""
    nombre: str
    especie: str
    edad: int
    sexo: str
    raza: str
    color: str
    senia: str
    peso: int | float
    # Permitimos NoNe para que la API no falle si el dato no viene del Frontend.
    # La IA usará este 'null' para sugerir completar la ficha.
    esterilizado: bool | None = None
    tiene_microchip: bool | None = None
    num_microchip: Optional[str] = None

class Visitas(BaseModel):
    """Registro de consultas médicas."""
    fecha: str
    motivo_consulta: str
    diagnostico:Optional[str] = None
    tratamiento: Optional[str] = None
    observaciones: Optional[str] = None
    historial_previo: Optional[bool] = None

class Vacunas(BaseModel):
    """Registro de inmunizaciones."""
    tipo: str
    nombre_cientifico: str
    fecha_aplicacion: str
    observacion: Optional[str] = None

class DatosClinicos(BaseModel):
    """Contenedor de toa la historia clinica para enviar a la IA."""
    paciente: Paciente
    visitas: List[Visitas]
    vacunas: List[Vacunas]

class ResumeniaRequest(BaseModel):
    """Modelo principal para solicitar un nuevo resumen a la IA."""
    model: str = Field(default="meta/llama-3.3-70b-instruct", description="AI model to use")
    
    # Campos obligatorios vinculados al a base de datos.
    id_paciente: int = Field(... , description="ID del paciente")
    datos_clinicos: DatosClinicos = Field(... , description="Historial clinico")

    # Parámetros de control de la IA.
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=2.0, description="Sampling temperature")
    stream: Optional[bool] = Field(default=False, description="Enable streaming response")

# --- Modelos de Respuesta Estructurada (JSON) ---

class VacunaResponse(BaseModel):
    nombre: str
    fecha_aplicacion: str
    estado: str

class VisitaResponse(BaseModel):
    fecha: str
    motivo: str
    diagnostico: Optional[str] = None
    tratamiento: Optional[str] = None

class ResumenEstructurado(BaseModel):
    """Formato JSON que debe generar la IA para que el sistema lo entienda."""
    estado_general: str
    tipo_paciente: str
    sintesis_visitas: List[VisitaResponse]
    historial_vacunas: List[VacunaResponse]
    descripcion_clinica: str
    tratamiento_indicado: str
    factores_riesgo: List[str]
    puntos_clave_proximas_consultas: List[str]

class ResumeniaResponse(BaseModel):
    """Respuesta final del microservicio al cliente."""
    id_resumenia: str = Field(..., description="ID único del resumen")
    id_paciente: int = Field(..., description="ID del paciente asociado")
    resumen_completo : str = Field(..., description="Resumen narrativo generado por la IA")
    resumen_estructurado: ResumenEstructurado = Field(..., description="Datos extraidos en formato JSON")
    modelo: str = Field(..., description="Modelo utilizado para la generación")
    fecha_generacion: datetime = Field(default_factory=datetime.now, description="Fecha de creacion del resumen")
    
    usage: Optional[Dict[str, int]] = Field(default=None, description="Token usage information")
    model_config = ConfigDict(from_attributes=True)

# --- Modelos para Listado y Consultas ---

class ModeloRequest(BaseModel):
    """Schema para validar requests almacenados."""
    id_request_ia : str = Field(..., description="ID del request")
    id_paciente : int = Field(..., description="ID del paciente")
    datos_clinicos : DatosClinicos = Field(..., description="Historia clinica del paciente")
    fecha_request: datetime = Field(..., description="Fecha del request" )

class RequestsPaciente(BaseModel):
    """Lista de peticiones realizadas por un paciente."""
    data: List[ModeloRequest] 

class ModeloResumen(BaseModel):
    """Schema para validar resúmenes recuperados de la DB."""
    id_resumenia: str = Field(..., description="ID resumen IA")
    id_paciente : int = Field(..., description="ID del paciente")
    resumen_completo: str = Field(..., description="Texto completo del resumen")
    resumen_estructurado: ResumenEstructurado = Field(..., description="Resumen IA estructurado")
    fecha_generacion: datetime = Field(...,description= "Fecha de generacion del resumen IA") 

class ResumenesPaciente(BaseModel):
    """Lista de resúmenes generados para un paciente."""
    data: List[ModeloResumen]

# --- Modelos de Utilidad y Salud del Sistema ---

class ModelInfo(BaseModel):
    """Listado de modelos LLM."""
    id: str = Field(..., description="Model ID")
    name: Optional[str] = Field(default=None, description="Model display name")
    description: Optional[str] = Field(default=None, description="Model description")
    pricing: Optional[Dict[str, Any]] = Field(default=None, description="Pricing information")

class HealthResponse(BaseModel):
    """Respuesta para el monitoreo del estado del servicio."""
    status: str = Field(..., description="Estado del servicio")
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field(..., description="Application version")
    message: Optional[str] = Field(default=None, description="Additional status message")

class ErrorResponse(BaseModel):
    """Formato estandar para reportar errores al cliente."""
    error: str = Field(..., description="Error type")
    detail: Optional[str] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

class RootResponse(BaseModel):
    """Root endpoint response model."""
    message: str = Field(..., description="Bienvenido la gestor de Resumenes veterinarios IA")
    version: str = Field(..., description="Version 1.0")
    docs: str = Field(..., description="Documentación URL")
    health: str = Field(..., description="Health check URL")