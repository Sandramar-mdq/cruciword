# AGENTS.md - Reglas de Arquitectura y Desarrollo para CruciWord

## 1. Descripcion del Proyecto

CruciWord es una Aplicacion Web Progresiva (PWA) minimalista y accesible para memorizar vocabulario en ingles mediante crucigramas con proposito, disenada de forma inclusiva desde ninos iniciados en lectoescritura hasta adultos mayores.

## 2. Stack Tecnologico Obligatorio

- Backend: Python 3.11+ y FastAPI.
- Base de Datos y ORM: PostgreSQL (Neon) + SQLAlchemy + Alembic (migraciones).
- Frontend: HTML5 + Tailwind CSS + JavaScript vainilla (mobile-first responsivo).
- Audio: Web Speech API nativa del navegador (activacion estrictamente bajo clic del usuario).
- Testing: Pytest.

## 3. Reglas de Negocio y Filosofia (Innegociables)

- Cero friccion: Sin notificaciones persecutorias, sin cronometros punitivos y sin bloqueos temporales (time-locks). El avance es libre y a demanda (modelo Pull).
- Independencia total: Cero llamadas a APIs externas de Inteligencia Artificial en tiempo de ejecucion. Todas las pistas, definiciones y sinonimos provienen de la base de datos propia.
- Uso mixto (RBAC): Un estudiante puede entrenar con paquetes estandar y vincularse mediante codigo de clase a listas personalizadas de un profesor.
- Extensibilidad: El banco lexico (tabla Words) debe permanecer desacoplado de los crucigramas para soportar a futuro otros juegos (Memotex, tablas de sinonimos) y competencias grupales por turnos.
- Sostenibilidad: Mantener campos estructurales de control para monetizacion futura (tipo de cuenta, auspicios) sin bloquear funciones basicas del MVP.

## 4. Reglas Visuales y de Interfaz

- Estetica: Revista de pasatiempos / comic de alto contraste (bordes negros de 2px-3px, tipografia sans-serif grande en imprenta mayuscula).
- Regla cromatica 60-30-10: 60% fondo pastel segun tema ambiental, 30% celdas de escritura blanco puro (#FFFFFF) con texto negro (#000000), 10% acentos vibrantes solo en palabra activa.
- Teclado virtual propio: Integrado en pantalla, teclas grandes (minimo 48x48px), letras A-Z sin acentos ni signos.
- Nomenclatura legal: Prohibido usar nombres de marcas registradas en temas o paletas.

## 5. Convenciones de Trabajo para OpenCode

- Trabajar siempre en modo plan antes de modificar o crear archivos.
- Mantener codigo modular, limpio y tipado (type hints en Python).
- Validar cada cambio estructural con pruebas unitarias en Pytest antes de dar por cerrada una tarea.
- Nunca hardcodear credenciales; usar siempre variables de entorno (.env).
