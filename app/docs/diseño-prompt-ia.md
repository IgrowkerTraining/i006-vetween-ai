# Diseño del System Prompt

## 1. Objetivo

El sistema utiliza un **Large Language Model (LLM)** para generar un **resumen clínico veterinario asistido por IA** a partir de datos estructurados del historial del paciente.

El system prompt establece:

- el **rol clínico del modelo**
- **protocolos de seguridad**
- **reglas de evaluación médica**
- **formato de salida obligatorio**

Esto permite controlar el comportamiento del modelo y evitar respuestas incorrectas o inseguras.

---

# 2. Rol del Modelo

El modelo opera bajo el siguiente rol definido en el system prompt:

- **Asistente Veterinario MASTER**
- Prioridad absoluta en **seguridad clínica**
- Capacidad de **interpretar historial veterinario**
- Generación de **resúmenes clínicos profesionales**

Este rol restringe al modelo para evitar comportamientos fuera del dominio veterinario.

---

# 3. Protocolos de Seguridad

El prompt implementa varios mecanismos de seguridad:

### Restricción de cambio de rol
El modelo no puede modificar su rol ni el formato de salida.

### Validación del input
Antes de generar el resumen, el modelo debe verificar que:

- el input describe **un animal**
- existen **eventos médicos reales**
- no hay placeholders o datos basura

### Filtro de basura

Si el input contiene:

- texto basura
- placeholders (`"string"`, `"asdf"`)
- campos vacíos
- datos incoherentes

el modelo debe responder exclusivamente con:

```json
{ "error": "INPUT_INVALIDO" }

```
Esto evita generar contenido clínico sobre datos inválidos.


# 4. Reglas Clínicas
El system prompt incluye reglas para evitar interpretaciones incorrectas.

## Evaluación del estado del paciente
Reglas definidas:

- Si existe diagnóstico de cáncer, falla orgánica o infección grave, el estado no puede ser "Estable".

- El estado debe clasificarse como:

    - Reservado
    - Crítico

## Validación de dosis
Si un tratamiento contiene dosis incompatibles con el peso del animal:

- el tratamiento no debe incluirse

- se debe generar una alerta de seguridad

## Eliminación de frases subjetivas
El modelo debe ignorar afirmaciones optimistas sin respaldo clínico.

Ejemplo:

    "se va a poner mejor"

si los datos clínicos muestran gravedad.

# 5. Arquitectura del Resumen Narrativo
El campo resumen_completo sigue una estructura narrativa específica.

## Encabezado
Resumen clínico asistido por IA – [Nombre del paciente]

## Contenido
- Estado general
- Tipo de paciente
- Narrativa clínica
- Interpretación clínica
- Esquema de vacunación
- Antecedentes
- Puntos clave para próximas consultas

## La narrativa debe:
- integrar todas las visitas
- utilizar párrafos cortos
- mantener tono clínico profesional
- evitar información no clínica

# 6. Ejemplos de Respuesta
El prompt incluye ejemplos reales para guiar el comportamiento del modelo.

Ejemplos incluidos:
- Copito
- Lorenzo

Estos ejemplos funcionan como few-shot prompting, ayudando al modelo a replicar el estilo narrativo esperado.

# 7. Formato de Salida

El modelo debe devolver exclusivamente un objeto JSON con la siguiente estructura.
```json
{
  "resumen_completo": "...",
  "resumen_estructurado": {
    "estado_general": "",
    "tipo_paciente": "",
    "sintesis_visitas": [
      {
        "fecha": "",
        "motivo": "",
        "diagnostico": "",
        "tratamiento": ""
      }
    ],
    "historial_vacunas": [
      {
        "nombre": "",
        "fecha_aplicacion": "",
        "estado": ""
      }
    ],
    "descripcion_clinica": "",
    "tratamiento_indicado": "",
    "factores_riesgo": [],
    "puntos_clave_proximas_consultas": []
  }
}
```
No se permite texto fuera del JSON.

# 8. Validación de la Respuesta
La respuesta generada por el modelo se valida utilizando Pydantic.

La validación asegura:
- estructura JSON correcta
- presencia de campos obligatorios
- tipos de datos válidos

Si la respuesta no cumple el esquema esperado se descarta.

# 9. Beneficios del Diseño del Prompt
Este diseño aporta varias ventajas:
- control del comportamiento del modelo
- reducción de alucinaciones
- salida estructurada consistente
- mayor seguridad clínica
- mejor integración con sistemas backend