from app.core.logging import get_logger

logger = get_logger(__name__)

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