-- =====================================================
-- Database Schema
-- Project: Backend IA
-- Engine: PostgreSQL (Supabase)
-- =====================================================


-- Extension required for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- =========================================
-- TABLE: ia_request
-- =========================================
CREATE TABLE public.ia_request (
  id_request_ia uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  id_paciente integer NOT NULL,
  datos_clinicos jsonb NOT NULL,
  fecha_request timestamp DEFAULT CURRENT_TIMESTAMP,
  hash text UNIQUE
);


-- =========================================
-- TABLE: metricas_ia
-- =========================================
CREATE TABLE public.metricas_ia (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  momento timestamptz DEFAULT now(),
  resultado text,
  duracion double precision,
  mensaje_error text
);


-- =========================================
-- TABLE: resumen_ia
-- =========================================
CREATE TABLE public.resumen_ia (
  id_resumenia uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  id_paciente integer NOT NULL,
  id_request_ia uuid NOT NULL,
  resumen_completo text NOT NULL,
  resumen_estructurado jsonb NOT NULL,
  modelo varchar,
  fecha_generacion timestamp DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_request_ia
  FOREIGN KEY (id_request_ia)
  REFERENCES public.ia_request(id_request_ia)
);