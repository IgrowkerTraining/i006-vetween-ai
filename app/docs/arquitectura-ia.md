# Arquitectura del Microservicio de IA

## 1. Overview

El sistema utiliza una arquitectura de **microservicios** donde el procesamiento de Inteligencia Artificial se encuentra desacoplado del backend principal.

El backend principal está desarrollado en **Node.js**, mientras que el procesamiento de IA se implementa en un microservicio independiente construido con **Python y FastAPI**.

Esta separación permite:

- escalar el procesamiento de IA de forma independiente
- reducir el acoplamiento entre servicios
- optimizar costos de inferencia
- mantener el dominio clínico aislado

---

# 2. Arquitectura General


Frontend
│
▼
Backend Node.js
(API principal)
│
│ HTTP REST
▼
Microservicio IA
(Python + FastAPI)
│
├── Validación de datos clínicos
├── Generación de hash de request
├── Control de cache
├── Lógica de generación IA
│
▼
Proveedor de LLM
(OpenRouter / NVIDIA NIM)

│
▼
Base de datos
(Supabase / PostgreSQL)


---

# 3. Componentes del Sistema

## Frontend

Responsabilidades:

- interfaz de usuario
- carga de datos clínicos
- visualización de resúmenes generados

No interactúa directamente con la IA.

---

## Backend Node.js

Responsabilidades:

- autenticación de usuarios
- gestión de pacientes
- lógica de negocio
- orquestación de servicios
- consumo del microservicio IA

Este backend actúa como **cliente del servicio de IA**.

Comunicación:

* HTTP REST

Endpoint principal consumido:

* POST /informes/resumenia


---

## Microservicio IA (Python)

Tecnologías utilizadas:

- **FastAPI**
- **Pydantic**
- **Supabase/PostgreSQL**

Responsabilidades:

- validación de datos clínicos
- control de duplicación de requests
- generación de prompts clínicos
- integración con modelos LLM
- estructuración de respuestas
- persistencia de resultados

Este servicio está diseñado como un **servicio especializado de generación de resúmenes clínicos**.

---

# 4. Flujo de Generación de Resumen

Usuario
│
▼
Frontend
│
▼
Backend Node
│
│ POST /informes/resumenia
▼
Microservicio IA
│
├─ Validación de esquema
├─ Generación de hash
├─ Verificación de cache
│
├─ Si existe → devolver resultado
│
└─ Si no existe:
│
├─ Generar prompt clínico
├─ Llamar al proveedor LLM
├─ Validar respuesta
├─ Persistir resultado
│
▼
Devolver resumen



---

# 5. Persistencia de Datos

El microservicio de IA persiste información en **Supabase (PostgreSQL)**.

Tablas principales:

### ia_request

Almacena cada request enviado al modelo de IA.

Campos principales:

- id_request_ia
- id_paciente
- datos_clinicos
- hash
- fecha_request

---

### resumen_ia

Almacena los resúmenes generados.

Campos principales:

- id_resumenia
- id_paciente
- modelo
- resumen_completo
- resumen_estructurado
- fecha_generacion

---

# 6. Sistema de Cache

Para reducir costos de inferencia se utiliza un mecanismo de **deduplicación por hash**.

Proceso:

1. Se genera un hash del request
2. Se busca en base de datos
3. Si existe un resultado previo:
   - se devuelve el resumen almacenado
4. Si no existe:
   - se ejecuta el modelo de IA

Beneficios:

- menor costo de LLM
- menor latencia
- reutilización de resultados

---

# 7. Integración con Modelos LLM

El microservicio se conecta a proveedores externos de modelos de lenguaje.

Proveedores posibles:

- OpenRouter
- NVIDIA NIM
- OpenAI compatible APIs

Modelo utilizado:
* meta/llama-3.3-70b-instruct


La integración se realiza mediante **API HTTP**.

---

# 8. Validación de Datos

La validación de entrada se realiza utilizando **Pydantic**.

Se valida:

- estructura del paciente
- estructura de visitas
- estructura de vacunas
- coherencia de datos clínicos

Esto evita enviar información inválida al modelo de IA.

---

# 9. Manejo de Errores

El microservicio implementa manejo de errores para:

- timeout de IA
- respuestas inválidas del modelo
- errores de proveedor
- errores de validación

Ejemplos de códigos de error:

| Código | Error |
|------|------|
| 408 | AI_TIMEOUT |
| 422 | AI_INPUT_INVALID |
| 502 | AI_PROVIDER_ERROR |
| 500 | AI_UNKNOWN_ERROR |

---

# 10. Beneficios de la Arquitectura

Esta arquitectura ofrece varias ventajas.

### Escalabilidad

El microservicio IA puede escalar de forma independiente.

### Aislamiento del dominio IA

El procesamiento con modelos LLM se mantiene separado de la lógica de negocio principal.

### Reducción de costos

El sistema de cache evita ejecuciones repetidas del modelo.

### Mantenibilidad

Permite modificar la lógica de IA sin afectar el backend principal.

---

# 11. Posibles Mejoras Futuras

Algunas mejoras que pueden implementarse:

- cola de procesamiento con **RabbitMQ / Redis**
- procesamiento asíncrono
- streaming de respuestas
- observabilidad (logs + métricas)
- rate limiting
- versionado de prompts

---