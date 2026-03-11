# 🚀 Vetween AI: Python + FastAPI + NVIDIA NIM / OpenRouter

¡Bienvenido! Este es el **microservicio de inteligencia artificial de Vetween**, diseñado para procesar **historias clínicas veterinarias** y generar **resúmenes diagnósticos estructurados** utilizando **FastAPI** y **modelos de lenguaje avanzados**.

---

## 📋 Descripción del Proyecto

Esta es una **API REST completa con integración de IA** que incluye:

* **Backend:** Python 3.10+ + FastAPI + NVIDIA NIM / OpenRouter
* **Package Manager:** `uv` (ultra-rápido) o `pip` (tradicional)
* **AI Integration:** Motor híbrido (**Llama-3 / Mixtral**) para análisis clínico estructurado
* **Configuration:** Variables de entorno utilizando **Pydantic Settings**
* **Documentation:** Documentación automática con **Swagger UI** y **ReDoc**
* **Containerization:** **Docker** y **Docker Compose** listos para despliegue
* **Development Tools:** Persistencia y auditoría en **Supabase (PostgreSQL)** configuradas


## 🗂️ Estructura del Proyecto

```
i006-vetween-ai/
├── main.py                        # Punto de entrada de la aplicación FastAPI
├── app/                           # Paquete principal de la aplicación
│   ├── api/                       # Capa de presentación (endpoints HTTP)
│   │   ├── dependencies.py        # Dependencias compartidas de la API
│   │   └── v1/                    # Versión 1 de la API
│   │       ├── health.py          # Endpoint de health check
│   │       └── informes.py        # Endpoints para generación y consulta de informes IA
│   │
│   ├── config/                    # Configuración del proyecto
│   │   └── settings.py            # Variables de configuración (env, settings globales)
│   │
│   ├── core/                      # Componentes centrales reutilizables
│   │   ├── database.py            # Configuración y conexión a base de datos
│   │   ├── logging.py             # Configuración del sistema de logs
│   │   ├── prompt_manager.py      # Gestión y carga de prompts para la IA
│   │   ├── security.py            # Utilidades de seguridad
│   │   └── prompts/               # Prompts utilizados por los modelos de IA
│   │       └── system_prompt_llama_v3.txt  # Prompt del sistema para el modelo Llama
│   │
│   ├── models/                    # Modelos de datos
│   │   └── schemas.py             # Modelos Pydantic para requests y responses
│   │
│   ├── repositories/              # Acceso a datos (capa de persistencia)
│   │   └── ai_repository.py       # Operaciones de base de datos para resúmenes IA
│   │
│   ├── services/                  # Lógica de negocio
│   │   ├── ai_service.py          # Integración con el proveedor de IA
│   │   ├── gestion_vacunas.py     # Servicios de gestión de vacunas
│   │   └── vacunas_core.py        # Lógica central del sistema de vacunas
│   │
│   └── test/                      # Tests del proyecto
│       └── test_ia.py             # Tests de funcionalidad del módulo de IA
│
├── docs/                          # Documentación técnica del sistema
│   ├── architecture.md            # Arquitectura general del sistema
│   ├── interface-contract.md      # Contrato de interfaz entre backend Node y backend IA
│   ├── sequence-diagram.md        # Diagrama de secuencia del flujo de generación de informes
│   ├── ai-prompt-design.md        # Diseño y reglas del system prompt del modelo
│   └── adr.md                     # Architectural Decision Records (decisiones técnicas)
│
├── requirements.txt               # Dependencias del proyecto
├── Dockerfile                     # Imagen Docker de la aplicación
├── docker-compose.yml             # Orquestación de servicios con Docker Compose
├── env.example                    # Plantilla de variables de entorno
└── README.md                      # Documentación principal del repositorio
```

### 🛠️ Tecnologías Utilizadas

### ⚙️ Core Framework

* **Python 3.10+**
  Lenguaje de programación principal.

* **FastAPI**
  Framework web asíncrono de alto rendimiento para la construcción de APIs.

* **Pydantic V2**
  Validación estricta de datos clínicos (por ejemplo: peso, microchip, edad, etc.).

* **Supabase**
  Cliente para persistencia de auditoría y almacenamiento de resúmenes en **PostgreSQL**.

* **Passlib**: Utilidades de seguridad y hashing.

---

### 📦 Package Management

* **uv** *(recomendado)*
  Gestor de paquetes ultra-rápido para Python.

* **pip**
  Gestor de paquetes tradicional compatible con el proyecto.

* **pyproject.toml**
  Archivo de configuración moderno para dependencias y metadatos del proyecto.

---

### 🤖 AI Integration

* **NVIDIA NIM**
  Motor principal para el procesamiento clínico utilizando modelos como **Llama-3** o **Mixtral**.

* **OpenRouter**
  Gateway de respaldo para garantizar redundancia y disponibilidad de modelos.

* **httpx**
  Cliente HTTP asíncrono utilizado para consumir APIs de modelos de inteligencia artificial.


### 🧑‍💻 Development & Deployment

* **Docker**
  Contenerización de la aplicación para asegurar consistencia entre entornos de desarrollo y producción.

* **Docker Compose**
  Orquestación de múltiples servicios para levantar el entorno completo de la aplicación.

* **python-dotenv**
  Gestión de variables de entorno mediante archivos `.env`.

* **Logging**
  Sistema de logging estructurado para monitoreo y diagnóstico de la aplicación.

* **CORS**
  Soporte para **Cross-Origin Resource Sharing**, permitiendo que clientes externos consuman la API de forma segura.


## 🚀 Configuración Rápida

### Opción 1: Usando `uv` *(Recomendado)*

```bash
# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clonar repositorio
git clone <repository-url>

# Entrar al proyecto
cd i006-vetween-ai

# Crear archivo de entorno
cp .env.example .env

# Instalar dependencias
uv sync

# Ejecutar aplicación en modo desarrollo
uv run fastapi dev main.py
```

---

### Opción 2: Usando `pip` *(Método tradicional)*

```bash
# Clonar repositorio
git clone <repository-url>

# Entrar al proyecto
cd i006-vetween-ai

# Crear archivo de entorno
cp .env.example .env

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación en modo desarrollo
fastapi dev main.py
```

## ⚙️ Variables de Entorno

Antes de ejecutar la aplicación es necesario crear un archivo `.env` basado en `env.example` y completar las siguientes variables:

```env
# AI Providers Configuration
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Database Configuration (Supabase)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# FastAPI Configuration
APP_NAME=Vetween-Backend-IA
APP_VERSION=1.0.0
DEBUG=true

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# CORS Configuration
CORS_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]

# Logging Configuration
LOG_LEVEL=INFO
```

### 📌 Notas

* **NVIDIA_API_KEY**: clave de acceso al servicio de modelos de NVIDIA NIM.
* **OPENROUTER_API_KEY**: proveedor alternativo de modelos de lenguaje.
* **SUPABASE_URL / SUPABASE_KEY**: credenciales del proyecto Supabase donde se persisten los resúmenes clínicos y auditorías.
* **CORS_ORIGINS**: dominios permitidos para consumir la API desde frontend.
* **LOG_LEVEL**: nivel de logging de la aplicación (`DEBUG`, `INFO`, `WARNING`, `ERROR`).


## 📚 Documentación de la API

Una vez ejecutada la aplicación, podés acceder a la documentación interactiva en:

* **Swagger UI**
  `http://localhost:8000/docs`

* **ReDoc**
  `http://localhost:8000/redoc`

* **OpenAPI Schema**
  `http://localhost:8000/openapi.json`


## 📡 Endpoints de la API

### 📄 Informes

| Método   | Endpoint                                   | Descripción                                        |
| -------- | ------------------------------------------ | -------------------------------------------------- |
| **GET**  | `/api/v1/informes/models`                  | Lista los modelos de IA disponibles                |
| **GET**  | `/api/v1/informes/resumenia`               | Obtiene todos los resúmenes generados              |
| **POST** | `/api/v1/informes/resumenia`               | Genera un resumen clínico utilizando IA            |
| **GET**  | `/api/v1/informes/resumenia/{id_paciente}` | Obtiene los resúmenes asociados a un paciente      |
| **GET**  | `/api/v1/informes/request`                 | Lista todos los requests realizados a la IA        |
| **GET**  | `/api/v1/informes/request/{id_paciente}`   | Obtiene los requests de IA asociados a un paciente |

---

### ❤️ Health

| Método  | Endpoint         | Descripción                  |
| ------- | ---------------- | ---------------------------- |
| **GET** | `/api/v1/health` | Verifica el estado de la API |


## 🐳 Docker (Opcional)

### Usar Docker Compose para Desarrollo

```bash
# Configurar variables de entorno
cp env.example .env
# Editar .env con tu API key

# Iniciar aplicación con Docker
docker-compose up --build

# Ejecutar en modo detached
docker-compose up --build -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Reconstruir y empezar
docker-compose up --build --force-recreate
```

### Docker Manual

```bash
# Construir imagen
docker build -t fastapi-ai-template .

# Ejecutar contenedor
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_api_key_here \
  fastapi-ai-template
```

## 🧪 Testing

### Con uv

```bash
# Instalar dependencias de desarrollo
uv sync --dev

# Ejecutar tests
uv run pytest

# Con coverage
uv run pytest --cov=.
```

### Con pip

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest
```

## 📈 Ventajas de uv vs pip

### uv (Recomendado)

- **10-100x más rápido** en instalación de dependencias
- Mejor resolución de dependencias
- Cache inteligente
- Integración nativa con pyproject.toml
- Gestión automática de entornos virtuales

### pip (Tradicional)

- Compatible con proyectos existentes
- Ecosistema maduro
- Familiar para la mayoría de desarrolladores

## 🔍 Ejemplos de Uso

### 🐍 Cliente Python (Uso del Servicio)

Este ejemplo utiliza los **esquemas definidos en `schemas.py`**.
El `AIService` procesa los datos clínicos, valida la lógica veterinaria y genera un **resumen clínico estructurado**.

```python
import asyncio
from app.services.ai_service import AIService
from app.models.schemas import ResumeniaRequest, DatosClinicos, Paciente, Visitas, Vacunas

async def ejecutar_resumen_profesional():
    ai_service = AIService()
    
    # Datos del Paciente siguiendo estrictamente el esquema Pydantic
    paciente_data = Paciente(
        nombre="Roco",
        especie="Canino",
        edad=4,
        sexo="Macho",
        raza="Ovejero Alemán",
        color="Negro y Fuego",
        senia="Cicatriz en pata trasera izquierda",
        peso=32.5,
        esterilizado=True,
        tiene_microchip=True,
        num_microchip="985112000123456"
    )
    
    # Historial de visitas y vacunas
    datos_clinicos = DatosClinicos(
        paciente=paciente_data,
        visitas=[
            Visitas(
                fecha="2025-02-20",
                motivo_consulta="Control de cadera",
                diagnostico="Displasia leve",
                tratamiento="Condroprotectores"
            )
        ],
        vacunas=[
            Vacunas(
                tipo="Antirrábica",
                nombre_cientifico="Rabisin",
                fecha_aplicacion="2024-11-15"
            )
        ]
    )
    
    # Request para la IA
    request = ResumeniaRequest(
        id_paciente=101,
        datos_clinicos=datos_clinicos,
        model="nvidia/llama-3.1-405b-instruct",
        temperature=0.2
    )

    try:
        resultado = await ai_service.generar_resumenia(
            request=request,
            id_request_ia=500,
            fecha_actual="2025-03-09T22:00:00"
        )

        print(f"Resumen guardado con ID: {resultado['id_resumenia']}")

    finally:
        await ai_service.close()

if __name__ == "__main__":
    asyncio.run(ejecutar_resumen_profesional())
```

---

### 🌐 Cliente `curl` (Payload Completo)

Ejemplo de request HTTP enviando un JSON completo respetando todos los campos definidos en `schemas.py`.

```bash
curl -X POST "http://localhost:8000/api/v1/informes/resumenia" \
  -H "Content-Type: application/json" \
  -d '{
    "id_paciente": 101,
    "datos_clinicos": {
      "paciente": {
        "nombre": "Luna",
        "especie": "Felino",
        "edad": 2,
        "sexo": "Hembra",
        "raza": "Siamés",
        "color": "Point",
        "senia": "Ojos azules intensos",
        "peso": 4.2,
        "esterilizado": true,
        "tiene_microchip": false
      },
      "visitas": [],
      "vacunas": []
    }
  }'
```
### 📄 Respuesta Esperada (Ejemplo)

El endpoint devuelve un resumen clínico generado por IA junto con una estructura organizada para facilitar su análisis.

```json id="j9slx8"
[
  {
    "id_resumenia": "string",
    "id_paciente": 0,
    "resumen_completo": "string",
    "resumen_estructurado": {
      "estado_general": "string",
      "tipo_paciente": "string",
      "sintesis_visitas": [
        {
          "fecha": "string",
          "motivo": "string",
          "diagnostico": "string",
          "tratamiento": "string"
        }
      ],
      "historial_vacunas": [
        {
          "nombre": "string",
          "fecha_aplicacion": "string",
          "estado": "string"
        }
      ],
      "descripcion_clinica": "string",
      "tratamiento_indicado": "string",
      "factores_riesgo": [
        "string"
      ],
      "puntos_clave_proximas_consultas": [
        "string"
      ]
    },
    "fecha_generacion": "2026-03-10T01:19:41.639Z"
  }
]
```

### 📌 Campos principales

* **id_resumenia**: identificador único del resumen generado.
* **id_paciente**: identificador del paciente asociado.
* **resumen_completo**: texto completo generado por el modelo de IA.
* **resumen_estructurado**: versión organizada del diagnóstico clínico.
* **fecha_generacion**: timestamp de generación del resumen.

El campo **`resumen_estructurado`** facilita el procesamiento por otros sistemas clínicos o dashboards.

## Database

PostgreSQL (Supabase)

Tablas:

- ia_request → registro de solicitudes a IA
- resumen_ia → resultados generados
- metricas_ia → métricas de ejecución

Schema disponible en:

database/schema.sql


## 🚀 Despliegue en Producción

### ⚙️ Variables de Entorno en Producción

Asegurate de configurar estas variables en tu entorno de producción (por ejemplo **Render** o **Railway**):

```env
NVIDIA_API_KEY=tu_api_key_secreta
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

SUPABASE_URL=tu_url_de_proyecto
SUPABASE_KEY=tu_service_role_key

DEBUG=false
APP_NAME=Vetween-Backend-IA
```

---

### 🔐 Consideraciones de Seguridad

* Nunca exponer el archivo `.env` en el control de versiones (debe estar incluido en `.gitignore`).
* Utilizar **API keys restringidas y rotativas** en producción.
* Configurar `CORS_ORIGINS` únicamente con el dominio del **frontend en producción**.
* Implementar **validación estricta con Pydantic** para prevenir inyecciones o datos malformados.
* Asegurar que todas las comunicaciones externas utilicen **HTTPS**.

---

## 🤝 Contribuir

1. Hacer **fork** del repositorio.
2. Crear una nueva rama de feature:

```bash
git checkout -b feature/nueva-funcionalidad-clinica
```

3. Realizar los cambios y hacer commit:

```bash
git commit -am "Agregar procesamiento de vacunas"
```

4. Subir los cambios al repositorio:

```bash
git push origin feature/nueva-funcionalidad-clinica
```

5. Crear un **Pull Request** hacia la rama:

```
develop-llamaIA
```

---

## 📝 Licencia

Este proyecto está bajo la **Licencia MIT**.
Ver el archivo `LICENSE` para más detalles.

---

## 🔗 Enlaces Útiles

* FastAPI Documentation
  https://fastapi.tiangolo.com/

* NVIDIA NIM API
  https://build.nvidia.com/

* OpenRouter API
  https://openrouter.ai/docs

* Supabase Documentation
  https://supabase.com/docs

* uv Documentation
  https://github.com/astral-sh/uv

---

## 🐾 Vetween AI

El motor de IA de **Vetween** está listo para procesar **historias clínicas veterinarias** y generar **resúmenes diagnósticos estructurados**.

🚀
