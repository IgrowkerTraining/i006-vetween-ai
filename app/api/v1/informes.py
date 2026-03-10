""" 
Módulo de rutas para la gestión de informes clínicos generados por IA.
Este router maneja la comunicación con OpenRouter y la persistencia de resúmenes
"""

from fastapi import APIRouter, HTTPException, Depends,status
from typing import List

from app.models.schemas import (
    ModeloResumen,
    ModeloRequest, 
    ResumeniaRequest, 
    ResumeniaResponse, 
    ModelInfo
)
from app.services.ai_service import AIService

import app.repositories.ia_repository as db_ia
from app.api.dependencies import get_ai_service
from app.core.logging import get_logger
import time

# Configuración de Logger y Router
logger = get_logger(__name__)
router = APIRouter(prefix="/informes", tags=["informes"])

#-----------------------------------------------------------------------------------
# ENDPOINTS DE DIAGNOSTICO (Utilidades)
#-----------------------------------------------------------------------------------

@router.get("/models", response_model=List[ModelInfo])
async def list_models(ai_service: AIService = Depends(get_ai_service)):
    """
    Obtiene el listado de modelos disponibles desde el proveedor (OpenRouter).
    Sirve para verificar la conectividad con la API externa.
    """
    try:
        models = await ai_service.list_models()
        return models
    except Exception as e:
        logger.error(f"Error al obtener modelos: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error de conexión con el proveedor {str(e)}"
            )

#-----------------------------------------------------------------------------------    
# ENDPOINTS DE NEGOCIO (Gestión de informes)
#-----------------------------------------------------------------------------------

@router.post("/resumenia", response_model=ResumeniaResponse)
async def resumen_ia(request: ResumeniaRequest, ai_service: AIService = Depends(get_ai_service)):
    """
    Genera un nuveo resumen clínico utilizando IA.
    1. Registra la petición en la base de datos (Input).
    2. Envía los datos clínicos al modelo seleccionado.
    3. Persiste el resumen generado por la IA en la base de datos (Output).
    4. Devuelve el análisis procesado al cliente.
    """

    #----- INICIO CRONOMETRO --------
    inicio_c = time.perf_counter()
    resultado_metrica = "FALLO_DESCONOCIDO"
    error_msg = None

    try:
        logger.info(f"Procesando resumen con modelo: {request.model}")
        
        # Guardar registro de la solicitud (input)
        guardar_request = await db_ia.save_request(
            request.id_paciente,
            request.datos_clinicos
        )
        if not guardar_request:
            # Si es None, enviamos al cliente el resumen persistido para ese request exacto
            resultado_metrica = "CACHE_HIT"
            id_paciente = int(request.id_paciente)
            data = db_ia.total_resumenes_ia_paciente(id_paciente)
            return data[0]
        else:
            resultado_metrica = "CACHE_MISS"
            id_request = guardar_request["id_request_ia"]
            fecha_actual = guardar_request["fecha_request"]
        
        # Generación y persistencia automática del resumen (Output)
        # Nota: 'generar_resumenia' internamente guarda el resultado en DB
            data = await ai_service.generar_resumenia(
                request,
                id_request,
                fecha_actual
                )
            return data
    
    except ValueError as e:
        resultado_metrica = "FALLO"
        error_msg = str(e)

        try:
            db_ia.eliminar_registro(id_request)
            logger.info(f"Registro {id_request} eliminado por fallo en IA.")
        except Exception as delete_error:
            logger.error(f"No se pudo limpiar el registro fallido: {str(delete_error)}")
        
        # Mapeo de errores específicos del servicio de IA
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

    finally:
        fin_c = time.perf_counter()
        latencia = fin_c - inicio_c

        db_ia.registrar_metricas_db(
            resultado= resultado_metrica,
            segundos= latencia,
            error= error_msg
        )

@router.get("/resumenia", response_model=List[ModeloResumen])
def listar_todos_los_resumenes():
    """
    Recupera el historial completo de resúmenes generados por la IA en el sistema.
    """
    try:
        return db_ia.total_resumenes_ia()
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail="Error al acceder a la base de datos de resúmenes"
        )

@router.get("/resumenia/{id_paciente}", response_model=list[ModeloResumen])
def resumenes_paciente(
    id_paciente : int , 
    ):
    
    """
    Obtiene todos los informes/resúmenes generados para un paciente específico.
    """
    try:
        # 1. Llamada al servicio: consultamos la persistencia (DB) filtando por ID de paciente
        data = db_ia.total_resumenes_ia_paciente(id_paciente)
        
        # 2. Validación de existencia: si la lista vuelve vacia, informamos al cliente
        # Es importante distinguir ente un error de servidor y un dato no encontrado (404)
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No hay historial de informes para el paciente ID: {id_paciente}"
            )
        # 3. Retorno de datos: FastAPI se encarfa de serializar la lista 'data' a formato JSON
        return data
    
    except ValueError:
        # 4. Manejo de excepciones: capturamos errores de lógica de negocio o de base de datos
        # Respondemos con un 500 para indicar que el problema fue del lado del servidor
        raise HTTPException(
            status_code=500,
            detail="Error al consultar el historial del paciente"
        )

#---------------------------------------------------------------------------------------
# ENDPOINTS DE PERSISTENCIA (Logs de Solicitudes)
#---------------------------------------------------------------------------------------

@router.get("/request", response_model=List[ModeloRequest])
def listar_requests():
    """
    Lista todos los logs de peticiones enviadas (Input original del usuario).
    """
    try:
        # 1. Recuperamos la totalidad de los inputs enviados a la IA.
        # Útil para auditoria y ver qué datos están enviando los usuarios.
        return db_ia.total_requests()
    
    except Exception as e:
        # 2. logueamos el error técnico para el desarrollador.
        logger.error(f"Error al cargar datos: {str(e)}")
        # 3. Respondemos un mensaje genérico al cliente por seguridad.
        raise HTTPException(
            status_code=500,
            detail=f"No se pudieron cargar los registros de peticiones. {str(e)}")


@router.get("/request/{id_paciente}", response_model=list[ModeloRequest])
def requests_paciente(
    id_paciente : int , 
):
    
    """
    Lista los logs de peticiones de un paciente específico.
    """
    try:
        # 1. filtramos los inputs originales en la base de datos por el ID del paciente
        data = db_ia.total_request_paciente(id_paciente)
        
        # 2. Control de flujo: Si el paciente existe pero nunca envió nada a la IA
        # devolvemos un 404 para indicar ausencia de datos
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No se registraron peticíones para el paciente ID: {id_paciente}"
            )
        
        # 3. Retornamos la lista de objetos 'ModeloRequest'
        return data
    
    except ValueError:
        # 4. En caso de error en la consulta o falla de base de datos.
        raise HTTPException(
            status_code=500,
            detail="Error al consultar los registros del paciente"
        )

