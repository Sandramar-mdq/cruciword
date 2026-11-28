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

## 🎨 Etapa 3 (Frontend): TAREA 1 y TAREA 2 — Estructura Base/PWA y Sistema Cromático (Noviembre 2026)
- **Estado:** Completada y validada.
- **TAREA 1 — Estructura Base Frontend y PWA:**
  - Layout Jinja2 modular en `templates/base.html` con `templates/index.html` y parciales `partials/header.html`, `partials/footer.html` y `partials/theme_switcher.html`; idioma `es`, viewport mobile-first, enlace al manifest, iconos y meta `theme-color`.
  - `app/main.py` registra `Jinja2Templates`, monta `StaticFiles` en `/static`, expone la ruta raíz `/` con el contexto de temas de `app/core/themes.py` y registra el MIME `font/woff2` para que los navegadores carguen la fuente local sin advertencias.
  - Tailwind CSS 3.4.17 integrado sin CDN: `tailwind.config.js` escanea plantillas y JS, `static/css/tailwind-input.css` es la entrada y `npm run build:css` genera `static/css/tailwind.css` autocontenido para uso offline.
  - `static/manifest.json`: nombre `Cruciword`, `display: standalone`, `orientation: any`, `start_url: /`, `scope: /` y colores `#F7EFD9` acordes al tema base; iconos `icon.svg`, `icon-192.png`, `icon-512.png` e `icon-maskable-512.png`.
  - `static/sw.js`: precaché de shell, CSS, JS, fuentes, iconos y manifest; estrategia **Cache-First** para assets estáticos, fallback transparente a la copia cacheada de `/` en navegaciones y paso directo de `/api/` para no inventar respuestas offline; se omite el precaché de datos dinámicos para no simular progreso.
  - `static/js/storage.js` centraliza `localStorage` bajo `cruciword:theme`, `cruciword:progress` y `cruciword:sync-queue`, con API para guardar progreso por crucigrama y encolar/colgar envíos pendientes sin perder datos al quedarse sin red.
  - `static/js/theme-init.js` aplica el tema guardado antes del primer pintado; `static/js/theme.js` conmuta temas sin recargar y sincroniza `aria-pressed` y el `meta[name="theme-color"]`; `static/js/app.js` registra el service worker y muestra un estado de conexión discreto, sin notificaciones persecutorias.
- **TAREA 2 — Sistema Cromático 60-30-10 y Estética Cómic:**
  - Balsamiq Sans 400/700 alojada en `static/fonts/` (latin y latin-ext, WOFF2) con su licencia OFL; `static/css/themes.css` declara los `@font-face` y la aplica a toda la interfaz con groteso amplio y interlineado cómodo para niños y adultos mayores.
  - Tokens por tema en `themes.css`: 60% de fondo cálido (`--cw-bg`), 30% de tarjetas y celdas (`--cw-card`, `--cw-cell: #ffffff` con `--cw-cell-ink: #000000`) y 10% de acento (`--cw-accent`) reservado a foco, palabra activa y aciertos.
  - Tres temas ambientales conmutables en caliente: **Papel Crema** (por defecto, `#F7EFD9`), **Edición Domingo** (`#F0EBE1`) y **Pizarra Nocturna** (`#1C1E1B`, mate); contraste AAA verificado para texto sobre fondo y tarjetas (16.4:1, 14.6:1 y 14.9:1 respectivamente; 21:1 en celdas blancas con tinta negra).
  - Estética de revista de pasatiempos: bordes sólidos de `2px`, sombras duras `3px 3px 0`, bocadillo de pista con cola, títulos en imprenta mayúscula, focos visibles de `3px` y controles de al menos `48px`; se respeta `prefers-reduced-motion`.
  - Sin APIs externas de IA ni CDNs en tiempo de ejecución: pistas, fuentes, iconos y estilos salen del propio servidor; el avance sigue siendo libre y a demanda (modelo Pull).
- **Verificación de cierre:**
  - `python -m pytest -q`: 92 tests pasados (17 nuevos en `tests/test_frontend.py`).
  - `python -m ruff check .`: sin advertencias ni errores; `python -m compileall -q app tests`: correcto.
  - `node --check` sobre los cuatro JS: sintaxis válida.
  - Smoke con `uvicorn` real: `/`, `/static/manifest.json`, CSS de Tailwind y temas, `storage.js`, `sw.js`, `icon.svg` y WOFF2 responden `200`; la fuente se sirve como `font/woff2`.
   - Pendiente para TAREA 3: `HU-04` (teclado virtual A-Z de teclas grandes) y la integración de partidas con el backend.

---

## Etapa 4: Niveles A1-C1, grillas coherentes y verificación instantánea (Noviembre 2026)
- **Estado:** Completada y validada.
- **TAREA 1 — Consolidación de niveles y grillas matemáticamente coherentes:**
  - `app/data/grids.py` centraliza cinco especificaciones puras, una por nivel: A1 `5x5` con `APPLE`/`CAT`, A2 `6x6` con `HOUSE`/`FOOD`/`FRIEND`, B1 `7x7` con `JOURNEY`/`MEMORY`/`MARKET`/`WEATHER`, B2 `11x11` con `ACHIEVEMENT`/`RELIABLE`/`ESTIMATE`/`PERSPECTIVE` y C1 `13x13` con `SOPHISTICATED`/`RESILIENT`/`NUANCE`/`AMBIGUITY`.
  - `build_grid_data()` deriva `grid_size`, `clues`, `placements` y `blocked_cells` desde posiciones explícitas; `validate_grid_data()` rechaza palabras fuera de límites, cruces incompatibles, longitudes inconsistentes y bloqueos que no corresponden a celdas ocupadas.
  - `app/db/seed.py` reutiliza el mismo builder, manteniendo 25 palabras y 5 crucigramas idempotentes; la migración data-only `9f2a6c1d4b70` reemplaza `grid_data` en bases ya sembradas y su `downgrade()` restaura las grillas anteriores.
  - Las pistas y sinónimos salen del banco léxico local; no hay llamadas a IA externa ni generación en tiempo de ejecución.
- **TAREA 2 — Verificación instantánea, feedback y puntuación sin fricción:**
  - `POST /api/puzzles/{puzzle_id}/check` valida letras y palabras en el servidor, sin autenticación ni persistencia, y devuelve estados booleanos por letra; nunca devuelve las soluciones.
  - `static/js/board.js` renderiza la grilla real desde `GET /api/puzzles/{id}`, permite filtrar por A1-C1, enfocar pistas, y verifica cada cambio de `cruciword:boardchange` con un debounce técnico de `120ms` (sin cronómetro visible).
  - `static/css/themes.css` añade esmeralda `--cw-success: #075c43` para aciertos y amarillo `--cw-attention: #f5c518` para letras que necesitan otra mirada, con textos AAA en los tres temas; no hay rojo, penalizaciones ni mensajes de fallo.
  - La mejor marca vive en `cruciword:progress` (`bestScore`) para jugar sin cuenta y se refleja en `UserProgress` al sincronizar; `score`, `is_completed` y `power_badge_earned` nunca retroceden.
  - `static/sw.js` sube a `cruciword-static-v3` y precachea `board.js`; el tablero mantiene fallback server-side en Jinja para lectores sin JS.
- **Verificación de cierre:**
  - `python -m pytest -q`: 121 tests pasados (nuevos `tests/test_grid_specs.py`, contratos `/check`, puntuación personal, contraste AAA y controles de nivel).
  - `python -m ruff check .`: sin advertencias ni errores; `python -m compileall -q app tests`: correcto.
  - `node --check` sobre `board.js`, `api.js` y `keyboard.js`: sintaxis válida.
  - Smoke de Alembic en SQLite temporal: `upgrade head`, `downgrade -1`, `upgrade head` y seed posterior; `placements` presente tras la última subida.

---

## 🎯 Etapa 3 (Frontend): TAREA 3 y TAREA 4 — Maquetación adaptativa, teclado y sincronización PWA (Noviembre 2026)
- **Estado:** Completada y validada.
- **TAREA 3 — Maquetación Fluida y Adaptativa (Mobile-First):**
  - `templates/index.html` incorpora tres parciales nuevos: `partials/game_demo.html` (tablero de práctica y bocadillo de pista activo), `partials/virtual_keyboard.html` (A–Z) y `partials/auth_panel.html` (acceso opcional en la portada, sin diálogos que interrumpan).
  - `static/js/keyboard.js` cierra `HU-04` a nivel de interfaz: 26 teclas grandes en mayúsculas, escritura por toque y simultáneamente por teclado físico (`A-Z`, `Backspace`/`Delete`, flechas, `Home`/`End`); ignora atajos con modificadores y nunca captura teclas dentro de formularios o campos editables.
  - Cada celda y tecla mide al menos `48x48px`; la celda activa se marca con el acento 10% y `aria-current`, con estados anunciados por `role="status"` y mensajes alentadores sin cronómetros.
  - `static/js/audio.js` activa la lectura de pistas solo bajo clic del usuario mediante `SpeechSynthesisUtterance` del navegador (`en-US`, velocidad `0.85` para niños y adultos mayores); alterna `aria-pressed`, guarda la preferencia en `cruciword:clues-audio` y no realiza ninguna llamada de red ni a IA externa.
  - `static/css/themes.css` añade una grilla de teclado de `5` columnas desde 360px, `9` en `sm` y `13` en `lg`, con `min-width:0`, `overflow-wrap`, `[hidden]`, focos visibles y sombras duras; el bocadillo activo usa borde grueso del color de acento sin romper la regla 60-30-10 ni los tres temas ambientales.
- **TAREA 4 — Conexión PWA con Autenticación y Sincronización de Estado:**
  - `static/js/api.js` centraliza `fetch` JSON con cabecera `Authorization: Bearer` cuando hay sesión: `register` (crea cuenta y entra automáticamente con el endpoint existente), `login`, `restoreSession` (`GET /api/users/me`), `loadPuzzles` (`GET /api/puzzles`) y `submitProgress` (`POST /api/puzzles/{id}/progress` con `power_mode_used: false`, `hints_used: 0` y clave `1_across`). El token vive en `cruciword:session` y nunca se registra en consolas ni mensajes.
  - `static/js/storage.js` incorpora `session` y `audio`, reutiliza `cruciword:progress` y `cruciword:sync-queue`. Si no hay red o el token devuelve `401`, la partida se guarda localmente y se encola; al volver la conexión o al entrar, `flushQueue()` drena la cola sin interrumpir al usuario, elimina solo respuestas `2xx` y ante `401` limpia la sesión invitando a entrar de nuevo sin bloquear el juego.
  - `static/js/app.js` dispara la sincronización al arrancar y en el evento `online`; `static/sw.js` sube a `cruciword-static-v2` y precachea `api.js`, `audio.js` y `keyboard.js`, manteniendo `/api/` fuera de la caché para no falsificar respuestas offline.
  - **Decisión de alcance:** no se añadió backend ni un `GET` de progreso porque la Etapa 2 solo expone escritura; el tablero sigue siendo una demo local que no hardcodea soluciones y envía las letras tecleadas al endpoint real para que el servidor evalúe con mensajes amables. La lectura remota de estado y la grilla real con ubicación de pistas quedan para una ampliación futura de la API.
- **Verificación de cierre:**
  - `python -m pytest -q`: 103 tests pasados (11 nuevos en `tests/test_frontend.py`).
  - `python -m ruff check .`: sin advertencias ni errores; `python -m compileall -q app tests`: correcto; Tailwind recompilado sin CDN.
  - `node --check` sobre los siete JS y arnés Node con DOM simulado: la partida offline quedó encolada, se drenó al recuperar red y envió el payload con `Bearer` y `power_mode_used: false`.
  - Smoke con `uvicorn` sobre Base SQLite temporal (borrada al finalizar): `/`, nuevos JS/CSS, `sw.js` y manifest en `200`; `register` `201`, `login` `200`, `GET /api/users/me` `200` y `POST /api/puzzles/1/progress` `200`.
  - El progreso devuelve `completed: false` porque la demo envía una sola palabra mientras el crucigrama semilla espera dos respuestas; el feedback sigue siendo informativo y no punitivo.
  - Trazabilidad: cerrados `HU-04` (teclado A-Z), `HU-01` (acceso opcional) y reforzados `RNF-01`, `RNF-02` y `RNF-03`.

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


## 🎨 Etapa 3: Interfaz Responsiva Multi-dispositivo y PWA (Noviembre 2026)

- **Estado:** Completada y validada.
- **Resumen Ejecutivo:** Implementación de la Interfaz Responsiva Multi-Dispositivo y PWA de *Cruciword* bajo estrictas directrices de arquitectura: cero llamadas a APIs externas de inteligencia artificial en tiempo de ejecución, diseño inclusivo y accesible (adaptado para niños y adultos mayores con tipografía amigable y alto contraste AAA), filosofía *pull* sin cronómetros punitivos, y soporte para funcionamiento offline mediante Service Worker y persistencia local.
- **Hitos alcanzados:**
  - **Estructura Base Frontend y PWA:**
    - Configuración del layout base modular en plantillas con Tailwind CSS compilado localmente.
    - Implementación del manifiesto (`static/manifest.json`) configurado en modo *standalone* con íconos limpios y la paleta cromática del proyecto.
    - Creación del Service Worker (`static/sw.js`) con estrategia *Cache-First* para assets estáticos y funcionamiento offline transparente.
    - Módulo `static/js/storage.js` para la persistencia local de preferencias de tema, estado de partidas y cola de sincronización.
  - **Sistema Cromático (60-30-10), Tipografía e Identidad Visual:**
    - Integración local de la tipografía gratuita y accesible Balsamiq Sans (`static/fonts/`), garantizando una lectura óptima y una estética de revista de pasatiempos.
    - Definición en `static/css/themes.css` de tres temas ambientales conmutables en tiempo real (*Papel Crema*, *Edición Domingo* y *Pizarra Nocturna*) aplicando la regla cromática 60-30-10, bordes sólidos de 2px y sombras duras (`3px 3px 0px #1E293B`).
  - **Maquetación Adaptativa y Ergonomía Táctil (Mobile-First):**
    - Diseño fluido sin desbordamientos horizontales desde 360px (móviles) hasta pantallas de escritorio.
    - Áreas táctiles garantizadas $\ge 48\text{px}$ tanto en celdas como en botones interactivos.
  - **Conectividad y Sincronización Base:**
    - Implementación del cliente `static/js/api.js` preparado para interactuar con los endpoints de autenticación y sincronización de estado del backend.
    - Mecanismo de reintento en segundo plano (`flushQueue` en `storage.js`) para manejar el estado de partidas de forma resiliente ante cortes de conectividad.
- **Validación de Calidad:**
  - Verificación estática y compilación de assets limpios.
  - Pruebas de compatibilidad responsiva en maquetación fluida.


---

## Anexo Técnico — Etapa 4: Motor de Crucigrama, Teclado Virtual y Validación Pull (CruciWord)

**Fecha:** 28 de noviembre de 2026  
**Estado:** Completado, verificado y confirmado en control de versiones (`main`)  
**Alcance:** Implementación integral del núcleo interactivo en frontend, interfaz táctil inclusiva, validación bajo demanda y matriz de calidad.

---

### 1. Arquitectura Modular y Motor de Grilla (`static/js/grid-engine.js` & `navigation.js`)
- **Normalización y Renderizado:** Estructuración del contrato de datos proveniente de FastAPI (`grid_size`, `blocked_cells`, `clues`, `placements`) hacia una grilla responsiva basada en CSS Grid.
- **Navegación Inteligente:**
  - Soporte para selección directa por clic o toque y alternancia automática de dirección (horizontal/vertical) en celdas de intersección.
  - Desplazamiento continuo con auto-avance al escribir, retroceso inteligente con `Backspace`/`Delete` y recorrido por teclado direccional (`ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`, `Home`, `End`).
  - Salto automático de celdas bloqueadas y delimitación estricta dentro de los bordes del tablero.

### 2. Interfaz Táctil Inclusiva y Soporte Físico (`static/js/keyboard.js` & `virtual_keyboard.html`)
- **Teclado Virtual QWERTY (`templates/partials/virtual_keyboard.html`):**
  - Disposición de 26 letras en filas QWERTY más botones de acción dedicada (borrado, cambio de dirección `⇄` y comprobación `✓`).
  - Áreas interactivas con dimensiones mínimas accesibles de `48px × 48px`, `touch-action: manipulation` y atributo `inputmode="none"` en las celdas para evitar el despliegue intrusivo del teclado nativo en dispositivos móviles.
  - Reglas de respaldo (*fallback*) definidas directamente en `static/css/themes.css` para eliminar dependencias de compilación en tiempo de ejecución.
- **Interoperabilidad con Teclado Físico:**
  - Captura acotada de `Tab` y `Space` exclusivamente cuando el foco reside dentro de una celda jugable del tablero (`[data-board-grid]`), preservando la navegación nativa accesible en el resto de la página.
  - Listener único en `keydown` que evita duplicación de eventos al combinar entradas táctiles y físicas.

### 3. Validación Instantánea "Pull" y Paleta Accesible (`static/js/board.js` & `themes.css`)
- **Flujo Sin Fricción:**
  - Eliminación completa de temporizadores automáticos (`debounce` y `setTimeout`). La petición `POST /api/puzzles/{id}/check` se dispara únicamente a demanda del usuario al accionar el botón `✓` (`CruciBoard.checkNow()`).
  - Limpieza sincrónica del estado visual (`clearFeedback()`) al modificar una letra, manteniendo las celdas acertadas editables para permitir correcciones libres.
- **Psicología del Color sin Penalización (Estándar WCAG AAA):**
  - **Acierto (`cw-cell--correct`):** Verde salvia suave (`#D1FAE5`) con texto de alto contraste (`#064E3B`, ratio `8.57:1`).
  - **Para revisar (`cw-cell--review`):** Ámbar cálido (`#FEF3C7`) con texto oscuro (`#78350F`, ratio `8.15:1`), aplicado únicamente sobre palabras con letras ingresadas.
  - Ausencia total de tonos rojos punitivos, cronómetros o límites de intentos.

### 4. Calidad, Pruebas Automatizadas y PWA
- **Suite de Verificación (149 tests aprobados):**
  - Cobertura unitaria y de integración distribuida en `test_grid_engine.py`, `test_grid_navigation.py`, `test_virtual_keyboard.py`, `test_instant_check.py` y la matriz de validación `test_stage4_matrix.py` (intersecciones, bordes, eventos sin duplicación, contraste AAA y *smoke test* de arranque).
  - Validación estática aprobada mediante `pytest`, `ruff check .`, `compileall` y `node --check` sobre todos los módulos JavaScript.
- **Service Worker (`static/sw.js`):** Actualización de la caché estática a `cruciword-static-v6` incluyendo los cuatro módulos principales del motor.
- **Control de Versiones:** Consolidación de todos los artefactos en un commit limpio bajo el mensaje `feat(cruciword): completar Etapa 4 - motor, navegacion, teclado virtual y validacion Pull`[cite: 3, 4, 8, 9, 10, 13].

---

