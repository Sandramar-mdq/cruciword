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

## ⚙️ Etapa 2: Backend, API REST y Gestión de Sesiones *(Próxima)*
- **Objetivo:** Desarrollo de endpoints en FastAPI, inyección de dependencias de base de datos, autenticación segura y lógica de negocio para la resolución de crucigramas y control de aulas.