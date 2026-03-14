# Contrato de Interfaz  
## Backend Node.js ↔ Backend Python IA

---

# 1. Introducción

Este documento define el **contrato de interfaz** entre el backend principal desarrollado en **Node.js** y el microservicio de **Inteligencia Artificial desarrollado en Python (FastAPI)**.

El objetivo de este contrato es **estandarizar la comunicación entre ambos servicios** para la generación de **resúmenes clínicos veterinarios mediante modelos de lenguaje (LLM)**.

El backend **Node.js** actúa como **cliente del servicio de IA**, mientras que el backend **Python** funciona como **microservicio especializado en procesamiento clínico con LLM**.

---

# 2. Arquitectura General
```
Frontend
│
▼
Backend Node.js (API principal)
│
│ HTTP REST
▼
Microservicio Python IA (FastAPI)
│
├─ LLM Provider (OpenRouter / NVIDIA NIM)
└─ Supabase (persistencia)
```

## Responsabilidades

| Servicio | Responsabilidad |
|--------|--------|
| Frontend | Interfaz de usuario |
| Backend Node.js | Orquestación del sistema, autenticación, lógica de negocio |
| Backend Python IA | Generación de resúmenes clínicos con LLM |
| Base de datos | Persistencia de requests y resultados |

---

# 3. Endpoint Principal

## Generar resumen clínico con IA

### Endpoint
POST /informes/resumenia


### Descripción

Este endpoint genera un **resumen clínico veterinario utilizando un modelo de lenguaje** a partir de los datos clínicos del paciente.

### Flujo interno del servicio

1. Recepción del request desde el backend Node  
2. Validación del esquema de entrada  
3. Generación de hash del request  
4. Verificación de existencia previa (cache)  
5. Evaluación clínica del contenido  
6. Ejecución del modelo LLM  
7. Validación de la respuesta generada  
8. Persistencia del resultado  
9. Devolución del resumen al cliente  

---



```json
{
  "model": "meta/llama-3.3-70b-instruct",
  "id_paciente": 123,
  "datos_clinicos": {
    "paciente": {
      "nombre": "Lorenzo",
      "especie": "canino",
      "edad": 5,
      "sexo": "macho",
      "raza": "Dachshund",
      "color": "marron",
      "senia": "mancha blanca en pecho",
      "peso": 8.5,
      "esterilizado": false,
      "tiene_microchip": true,
      "num_microchip": "AR123456"
    },
    "visitas": [
      {
        "fecha": "2026-03-18",
        "motivo_consulta": "control de peso",
        "diagnostico": "obesidad",
        "tratamiento": "dieta hipocalorica",
        "observaciones": "actividad fisica recomendada"
      }
    ],
    "vacunas": [
      {
        "tipo": "rabia",
        "nombre_cientifico": "Rabies vaccine",
        "fecha_aplicacion": "2025-10-01"
      }
    ]
  },
  "max_tokens": 1000,
  "temperature": 0.0,
  "frequency_penalty": 1.5,
  "presence_penalty": 0.5,
  "stream": false
}
```

# 5. Response

## Response Schema
```json

{
  "id_resumenia": "uuid",
  "id_paciente": 123,
  "modelo": "meta/llama-3.3-70b-instruct",
  "resumen_completo": "Texto narrativo generado por la IA",
  "resumen_estructurado": {
    "estado_general": "estable",
    "tipo_paciente": "canino adulto",
    "sintesis_visitas": [
      {
        "fecha": "2026-03-18",
        "motivo": "control de peso",
        "diagnostico": "obesidad",
        "tratamiento": "dieta hipocalorica"
      }
    ],
    "historial_vacunas": [
      {
        "nombre": "rabia",
        "fecha_aplicacion": "2025-10-01",
        "estado": "vigente"
      }
    ],
    "descripcion_clinica": "Paciente con obesidad moderada...",
    "tratamiento_indicado": "Plan nutricional controlado...",
    "factores_riesgo": [
      "obesidad",
      "sedentarismo"
    ],
    "puntos_clave_proximas_consultas": [
      "control de peso",
      "seguimiento nutricional"
    ]
  },
  "fecha_generacion": "2026-03-11T13:00:00"
}
```

# 6. Sistema de Cache por Hash

El servicio implementa un sistema de deduplicación de requests utilizando un hash del contenido clínico.

**Si el mismo request fue procesado previamente:**

* No se vuelve a invocar el modelo de IA
* Se devuelve el resultado persistido

**Esto reduce:**

* costos de inferencia
* tiempo de respuesta
* consumo de API externa

# 7. Endpoints Auxiliares

## Obtener modelos de IA disponibles
GET /informes/models
```json
[
  {
    "id": "meta/llama-3.3-70b-instruct",
    "name": "Llama 3.3 70B",
    "description": "Large language model"
  }
]
```

# Obtener todos los resúmenes generados
    GET /informes/resumenia

# Obtener resúmenes por paciente
    GET /informes/resumenia/{id_paciente}

# Obtener requests enviados a IA
    GET /informes/request

# Obtener requests por paciente
    GET /informes/request/{id_paciente}

# 8. Manejo de Errores

## El servicio devuelve errores HTTP estándar con mensajes descriptivos.

| Código | Error | Descripción |
| :--- | :--- | :--- |
| **408** | `AI_TIMEOUT` | La IA tardó demasiado en responder |
| **422** | `AI_INPUT_INVALID` | Caso clínico inválido |
| **502** | `AI_PROVIDER_ERROR` | Error del proveedor de IA |
| **502** | `AI_RESPONSE_INVALID` | Respuesta inválida del modelo |
| **500** | `AI_AUTH_ERROR` | Error de autenticación |
| **500** | `AI_UNKNOWN_ERROR` | Error interno del sistema |

Ejemplo:

```json
{
  "detail": "El contenido proporcionado no es un caso clínico veterinario válido."
}
```

# 9. Integración desde Backend Node.js

## El backend Node debe consumir el servicio mediante HTTP REST.

## Cliente recomendado
    axios

Ejemplo

```javascript
const axios = require("axios")

const response = await axios.post(
  "http://python-ai-service/informes/resumenia",
  payload
)

return response.data
Timeout recomendado
120 segundos
```

Los modelos LLM pueden requerir varios segundos para responder dependiendo del tamaño del contexto.

# 10. Reglas de Validación

Antes de enviar el request al microservicio IA, el backend Node debe asegurar:

## Campos obligatorios

* id_paciente

* datos_clinicos

* datos_clinicos.paciente

## Listas esperadas

* visitas

* vacunas

El microservicio Python también realiza validaciones adicionales utilizando Pydantic.

# 11. Versionado de la API

Para evitar incompatibilidades futuras se recomienda versionar los endpoints:
````
/api/v1/informes/resumenia

````
Esto permite introducir cambios sin romper integraciones existentes.

# 12. Beneficios de la Separación de Servicios

La arquitectura separa claramente responsabilidades.

## Backend Node

* gestión de usuarios

* autenticación

* lógica de negocio

* APIs públicas

## Backend Python IA

* procesamiento clínico

* integración con modelos LLM

* validación semántica

* generación de resúmenes

Esto permite escalar el servicio de IA de forma independiente.
