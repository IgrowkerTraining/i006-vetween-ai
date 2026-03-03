import unicodedata
from app.services.vacunas_core import  CORE_GROUPS
from app.models.schemas import Vacunas
from datetime import datetime
from dateutil.relativedelta import relativedelta

def normalizar_texto(texto: str) -> str:
    """
    Limpia y estandariza strings para comparaciones precisas.
    Remueve tildes, convierte a minusculas y elimina caracteres especiales.
    """
    # 1. LLevamos todo a minuscula
    texto = texto.lower()
    
    # 2. Descomponemos caracteres (ej: 'é' -> 'e' ->'´')
    texto = unicodedata.normalize("NFD", texto)

    # 3. Eliminamos tildes. Aseguramos que la busqueda no falle por un acento mal puesto
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto

def clasificar_vacuna(vacuna: Vacunas) -> str:
    """
    Asigna un grupo sanitario (CORE o RABIA) basandose en el nombre de la vacuna.
    Utiliza busqueda por palabras calve en los campos de tipo y nombre cientifico.

    """
    
    # 1. Preparación del input: Combinamos ambos campos para maximizar la probabilidad de match.
    # Si los campos vienen como None, usamos un string vacío para evitar errores de concatenación.
    texto = normalizar_texto(
        (vacuna.tipo or "") + " " +
        (vacuna.nombre_cientifico or "")
    )

    # 2. Match de Keywords: Iteramos el diccionario CORE_GROUPS buscando coincidencias.
    # Se prioriza el primer grupo encontrado según el orden definido en el diccionario.
    for grupo, data in CORE_GROUPS.items():
        for keyword in data["keywords"]:
            if keyword in texto:
                return grupo

# 3. Si no hay coincidencias, devolvemos un estado neutro para no sesgar a la IA.
    return "DESCONOCIDA"

def evaluar_vacunas(vacunas: list[Vacunas], fecha_actual: str):
    """
    Calcula la vigencia de cada vacuna y determina riesgos legales o sanitarios.
    Procesa las fechas en Python para entregar datos estructurados y precisos a la IA.
    """
    historial = []
    esquema_incompleto = False
    riesgo_legal = False

    try:
        # 1. Validación de Fecha Actual: Convertimos el string ISO del sistema a objeto datetime.
        # Este paso es crítico para poder realizar comparaciones matemáticas de tiempo.
        fecha_actual_dt = datetime.strptime(fecha_actual, "%Y-%m-%d")
        
        for vacuna in vacunas:
            try:
                # 2. Procesamiento Individual: Intentamos parsear la fecha de aplicación de cada vacuna.
                # Si el dato es un placeholder ("string", "asdf"), el bloque except interno lo captura.
                fecha_aplicacion = datetime.strptime(vacuna.fecha_aplicacion, "%Y-%m-%d")
                grupo = clasificar_vacuna(vacuna)


                if grupo != "DESCONOCIDA":
                # 3. Cálculo de Vencimiento: Se suma la vigencia en meses definida en la configuración.
                # El uso de relativedelta asegura un cálculo exacto de meses calendario.
                    meses = CORE_GROUPS.get(grupo, {}).get("vigencia_meses", 12)
                else:
                    meses = 12
                
                fecha_vencimiento = fecha_aplicacion + relativedelta(months=meses)

                # 4. Lógica de Flags: Comparamos contra la fecha de referencia para detectar vencimientos.
                if fecha_actual_dt > fecha_vencimiento:
                    estado = "VENCIDA"
                    esquema_incompleto = True
                    # Alerta Crítica: La rabia vencida implica un riesgo legal para el propietario.
                    if grupo == "RABIA":
                        riesgo_legal = True
                else:
                    estado = "AL_DIA"
                
                # 5. Estructuración: Creamos un diccionario limpio que la IA pueda interpretar fácilmente.
                historial.append({
                    "nombre": vacuna.tipo,
                    "grupo_sanitario": grupo,
                    "fecha_aplicacion": vacuna.fecha_aplicacion,
                    "estado": estado
                })
            except (ValueError, TypeError, KeyError):
                # Si una vacuna individual tiene basura, la ignoramos y seguimos
                continue

    except (ValueError, TypeError):
        # Si la fecha_actual es inválida, devolvemos el esquema base vacío
        print("Aviso: Error de formato en pre-procesamiento. Delegando validación a la IA.")
    
    return {
        "historial_vacunas": historial,
        "esquema_incompleto": esquema_incompleto,
        "riesgo_legal": riesgo_legal
    }