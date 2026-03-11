```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as Backend Node
    participant AI as Microservicio IA
    participant LLM as LLM Provider
    participant DB as Database

    FE->>API: Solicitar resumen clínico
    API->>AI: POST /informes/resumenia
    AI->>DB: Buscar hash del request

    alt Resultado existente
        DB-->>AI: devolver resumen existente
    else Nuevo resumen
        AI->>LLM: Enviar prompt clínico
        LLM-->>AI: Respuesta generada
        AI->>DB: Guardar resumen
    end

    AI-->>API: Resumen generado
    API-->>FE: Respuesta API