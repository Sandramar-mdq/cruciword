# 📚 Bitácora e Historial Técnico de CruciWord

Este documento recopila la evolución histórica, las decisiones de arquitectura y el estado de cada etapa completada en el desarrollo de la PWA **CruciWord**.

---

## 🚀 Etapa 1: Infraestructura, Base de Datos y Gobernanza (Noviembre 2026)
- **Estado:** Completada y versionada.
- **Hitos alcanzados:**
  - Definición de gobernanza y stack tecnológico estricto en `AGENTS.md`.
  - Especificación formal de Historias de Usuario (`HU-01` a `HU-09`) y Requerimientos No Funcionales en `REQUIREMENTS.md`.
  - Configuración de la persistencia relacional con PostgreSQL (Neon) y SQLAlchemy.
  - Ejecución exitosa de la migración inicial de Alembic (`af5ca72205b3`) contemplando modelos robustos (`Users`, `Classrooms`, `StudentClassrooms`, `Words`, `Puzzles`, `UserProgress`).
  - Validación de calidad con pruebas unitarias en `pytest` (7 tests pasados) y control estático con `Ruff`.
- **Reporte detallado:** [Ver reporte completo de la Etapa 1](./etapa-1-reporte.md)

---

## ⚙️ Etapa 2: Backend, API REST y Gestión de Sesiones (Noviembre 2026)
- **Estado:** Completada y validada integralmente.
- **Entregables completados:**
  - Configuración centralizada y persistencia desacoplada en `app/core/config.py`, `app/db/database.py` y `database.py` (shim), con SQLite local por defecto y Neon opcional vía `.env`.
  - Contratos Pydantic v2 en `app/schemas/` para autenticación, usuarios, crucigramas y aulas.
  - Seguridad JWT Bearer y hash bcrypt en `app/core/security.py` y `app/api/deps.py`, incluyendo el guardián `require_teacher`.
  - Endpoints registrados en `app/main.py`: `/api/auth`, `/api/users`, `/api/puzzles` y `/api/classrooms`.
  - Lógica de negocio sin IA externa en `app/services/puzzle_service.py` y `app/services/classroom_service.py`: evaluación amable de respuestas, insignia de Modo Power sin pistas y códigos de aula de 6 caracteres sin caracteres ambiguos.
  - Modelo de datos y migraciones: `af5ca72205b3` (esquema inicial), `5387d2f3cec0` (`power_badge_earned`) y `cefaaef187b6` (`classrooms.description`).
  - Suite aislada en 7 módulos de prueba (`test_auth.py`, `test_db_database.py`, `test_database_schema.py`, `test_schemas.py`, `test_puzzle_service.py`, `test_puzzles.py` y `test_classrooms.py`) con fixture compartida en `tests/conftest.py`.
- **Decisiones técnicas relevantes:**
  - El campo público `username` se mapea internamente a `users.email`; no se añadió una columna redundante.
  - Se fijó `bcrypt==4.0.1` por la incompatibilidad detectada entre `passlib 1.7.4` y versiones posteriores de bcrypt.
  - `ClassroomResponse.join_code` se mapea desde `Classroom.invite_code` y la unión repetida es idempotente sobre `student_classrooms`.
  - Las respuestas de detalle no exponen soluciones ni respuestas, y el feedback evita cronómetros, bloqueos y mensajes punitivos.
- **Trazabilidad de requerimientos:** cubiertos `HU-01`, `HU-02`, `HU-03`, `HU-05`, `HU-07` y `HU-08`. Quedan para etapas posteriores `HU-06` (test de retención) y `HU-09` (listas personalizadas de palabras).
- **Verificación de cierre (TAREA 6):**
  - `python -m pytest -q`: 58 tests pasados.
  - `python -m ruff check .`: sin advertencias ni errores.
  - `python -m compileall -q .`: compilación correcta; smoke de imports con 13 rutas FastAPI registradas.
  - Alembic: `upgrade head` y `check` sin nuevas operaciones, `downgrade base` correcto y SQL offline generado para PostgreSQL con las tres revisiones.
  - Head técnico vigente: `cefaaef187b6`.

---

## 🧱 Etapa 3: Backend complementario, datos semilla y cierre de HU-06/HU-09 (Noviembre 2026)
- **Estado:** Completada y validada.
- **Entregables completados:**
  - Seed idempotente ejecutable con `python -m app.db.seed`: 25 palabras (5 por nivel A1-C1) y 5 crucigramas base con pistas estáticas y soluciones server-side.
  - Listas personalizadas (`HU-09`) mediante `word_lists` y `word_list_words`, esquemas en `app/schemas/word_list.py` y endpoints en `app/api/routes/word_lists.py`.
  - Test de retención (`HU-06`) en `POST /api/puzzles/{puzzle_id}/retention`, con esquemas en `app/schemas/puzzle.py` y reutilización de `evaluate_progress`.
  - Migración Alembic `c4c813450fd6` con nuevas tablas, columnas de retención y constraints únicos de seed.
- **Decisiones técnicas relevantes:**
  - `WordList` mantiene `Word` desacoplado: las listas solo referencian `word_ids` existentes y no crean palabras nuevas.
  - La lectura está restringida al docente dueño o a estudiantes vinculados al aula; sin acceso se responde `404` para no filtrar datos.
  - La retención es libre y a demanda: no hay time-locks ni validación de semana; registra `retention_score` y `retention_completed_at` sin sobrescribir `score`, `hints_used` ni `power_badge_earned`.
- **Trazabilidad de requerimientos:** cerrados `HU-06` (test de retención) y `HU-09` (listas personalizadas). `HU-04` continúa pendiente en la Etapa 3 de frontend porque corresponde al teclado virtual A-Z.
- **Verificación de cierre:**
  - `python -m pytest -q`: 75 tests pasados.
  - `python -m ruff check .`: sin advertencias ni errores.
  - `python -m compileall -q .`: compilación correcta; smoke de imports con 17 rutas FastAPI registradas.
  - Alembic: `upgrade head`, `check`, `downgrade base` y SQL offline PostgreSQL sin errores; head vigente `c4c813450fd6`.
  - Seed ejecutado dos veces sobre SQLite temporal: 25 palabras y 5 crucigramas insertados, luego 25 y 5 omitidos.

---

## ⚙️ Etapa 2: Backend, API REST y Gestión de Sesiones (Noviembre 2026)
- **Estado:** Completada y validada.
- **Hitos alcanzados:**
  - Arquitectura modular bajo `app/` (`core`, `db`, `schemas`, `api/routes`, `services`).
  - Persistencia dual (SQLite local/testing y Neon PostgreSQL producción) con 3 revisiones de Alembic aplicadas (`af5ca72205b3`, `5387d2f3ec0`, `cefaafef187b`).
  - Seguridad JWT (`PyJWT`) y hashing `bcrypt`, con separación estricta de roles (`require_teacher`).
  - Lógica de validación de crucigramas y otorgamiento automático de insignia **Modo Power** (`hints_used == 0`).
  - Códigos de unión a aulas (`join_code`) de 6 caracteres sin ambigüedad visual (`0, O, 1, I`).
  - Validación completa: **58/58 tests unitarios** en `pytest`, `ruff` sin advertencias y 13 rutas FastAPI registradas.
- **Reporte detallado:** [Ver reporte completo de la Etapa 2](./etapa-2-reporte.md)

---

## ⚙️ Cierre de Pendientes de Backend: HU-06 (Retención) y HU-09 (Listas Personalizadas) (Noviembre 2026)
- **Estado:** Completado y validado.
- **Hitos alcanzados:**
  - Creación de modelos `word_lists` y relación M:N `word_list_words` desacoplados del banco léxico principal.
  - Incorporación de campos de retención (`retention_score`, `retention_completed_at`) en `UserProgress` sin bloqueos de tiempo (*time-locks*).
  - Migración de Alembic aplicada exitosamente (`c4c81345fd6`).
  - Script de datos semilla (`python -m app.db.seed`) idempotente con 25 palabras y 5 crucigramas (niveles A1 a C1).
  - Cobertura de pruebas ampliada a **75 tests unitarios** pasando al 100% con `pytest`, análisis estático limpio con `ruff` y 17 rutas FastAPI operativas.

---


