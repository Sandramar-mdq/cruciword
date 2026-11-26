# REQUIREMENTS.md - Especificación de Requerimientos e Historias de Usuario

## 1. Visión General

CruciWord es una Aplicación Web Progresiva (PWA) minimalista y accesible para memorizar vocabulario en inglés mediante crucigramas con propósito. Está diseñada de forma inclusiva para abarcar desde niños iniciados en lectoescritura hasta adultos mayores, bajo una filosofía de cero presiones y ritmo libre.

## 2. Historias de Usuario (User Stories)

### Módulo Estudiante (Core de Aprendizaje)

- HU-01 (Registro y Sincronización): Como estudiante, quiero registrarme con email y contraseña simple o iniciar sesión, para guardar mi progreso en la nube y continuar mis partidas en celular, tablet o PC indistintamente.
- HU-02 (Selección de Partida sin Fricción): Como usuario, quiero acceder a una pantalla selectora donde elija temática y nivel (A1 a C1) sin bloqueos temporales ni advertencias punitivas, para empezar a jugar de inmediato.
- HU-03 (Modo Power Opcional): Como usuario, quiero activar un interruptor opcional de Modo Power para sumar vocabulario coloquial o modismos adicionales al bloque semanal.
- HU-04 (Resolución y Teclado Virtual): Como usuario, quiero tocar celdas de la grilla e ingresar letras mediante un teclado virtual gigante integrado en pantalla (solo letras A-Z en imprenta mayúscula), para escribir con comodidad sin depender del teclado nativo del dispositivo.
- HU-05 (Pistas Estáticas y Audio Opcional): Como usuario, quiero disponer de hasta 3 pistas fijas por partida (sinónimo en inglés, categoría contextual o revelación de una letra) y un botón de pronunciación opcional bajo clic, para resolver dificultades sin depender de inteligencia artificial externa.
- HU-06 (Evaluación de Retención): Como usuario, quiero realizar un test rápido al finalizar un bloque de crucigramas para comprobar mi memorización del vocabulario trabajado.

### Módulo Profesor y Aulas (B2B / Vincular)

- HU-07 (Creación de Aulas): Como profesor, quiero registrarme con rol docente, crear cursos y obtener un código alfanumérico único para compartirlo con mis estudiantes.
- HU-08 (Uso Mixto del Estudiante): Como estudiante, quiero vincularme mediante un código de clase a un profesor para acceder a sus listas personalizadas, manteniendo la libertad de entrenar por mi cuenta con los bloques generales de la plataforma.
- HU-09 (Listas Personalizadas): Como profesor, quiero crear y asignar mis propias listas de palabras a mis aulas para utilizar la herramienta como instancia práctica o evaluación lúdica.

## 3. Requerimientos No Funcionales (RNF)

- RNF-01 (Accesibilidad y Estética): Estética de revista de pasatiempos / cómic de alto contraste (trazos negros marcados, tipografía grande en imprenta mayúscula) bajo la regla cromática 60-30-10 con temas ambientales pastel.
- RNF-02 (Independencia Técnica): Cero consumo de APIs externas de Inteligencia Artificial en tiempo de ejecución; toda la lógica opera desde base de datos propia para asegurar velocidad instantánea y bajo costo.
- RNF-03 (Diseño Responsivo): Adaptación fluida en pantallas verticales móviles, tablets y computadoras de escritorio sin desbordes de grilla ni teclado.
- RNF-04 (Extensibilidad): El banco de palabras debe permanecer desacoplado de las grillas de crucigramas para soportar futuras variantes de juego (Memotex, tablas de sinónimos) y competencias grupales por turnos.
- RNF-05 (Sostenibilidad): La arquitectura de datos debe prever campos estructurales para futura monetización (auspicios de bloques, packs temáticos y planes institucionales) sin afectar el acceso gratuito inicial.
