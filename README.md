# Genesis Mocap — Addon y tester integral

Herramientas para validar rigs Genesis 4C y probar el motor de visión desde una aplicación externa a Blender.

## Fase 1 — Base y validación de rigs

El addon instalable está en \`app/genesis_mocap\`. En Blender 5.x añade el panel **Genesis Mocap** a la Vista 3D, permite seleccionar un Armature y valida el perfil de 58 destinos: 52 huesos Genesis requeridos y 6 controles auxiliares.

El tester externo inspecciona archivos \`.blend\` con Blender en segundo plano, lista los objetos ARMATURE y permite validar el rig seleccionado. No instala el addon ni guarda o modifica el archivo original.

## Fase 2 — Motor de Visión

El motor está en \`app/genesis_mocap_tester/vision.py\` y usa MediaPipe Tasks Pose Landmarker. Admite los modos IMAGE (fotografía) y VIDEO (cámara/vídeo), con hasta 8 personas por defecto (configurable).

- Apertura y análisis de imágenes estáticas: PNG, JPG/JPEG, BMP y WEBP.
- Captura desde cámara conectada (índice configurable, normalmente 0).
- Apertura y reproducción de archivos de vídeo.
- Detección simultánea de varias poses humanas.
- Esqueleto dibujado sobre cada persona: conexiones corporales y puntos de articulación visibles.
- Rectángulos y etiquetas; el sujeto elegido queda resaltado en verde y los demás en amarillo.
- Lista y selector desplegable para elegir entre las personas detectadas.
- Panel de datos del sujeto: ID temporal, cantidad de puntos visibles, visibilidad media, caja delimitadora y coordenadas normalizadas de los puntos visibles.
- Opción para activar/desactivar el dibujo del esqueleto.

**Importante:** los números de persona son IDs temporales de seguimiento, no reconocimiento de identidad. Si alguien sale del encuadre, queda oculto o cruza con otra persona, el ID puede cambiar. La precisión depende de la iluminación, resolución, oclusiones y tamaño de la persona en la imagen. Esta fase no genera animaciones, keyframes ni retargeting.

### Modelo de visión

Se usa el modelo ligero oficial \`pose_landmarker_lite.task\`. En el primer inicio se descarga automáticamente si no existe. Se guarda en:

- Windows: \`%LOCALAPPDATA%\\GenesisMocap\\models\\pose_landmarker_lite.task\`
- Otros sistemas: \`~/GenesisMocap/models/pose_landmarker_lite.task\`

También puedes seleccionar un archivo \`.task\` local desde el tester. La descarga automática requiere Internet en el primer inicio.

## Tester integral (Fase 1 + Fase 2)

Las dos fases se prueban desde una sola aplicación y carpeta: \`app/genesis_mocap_tester\`.

### Requisitos

- Windows 10/11 de 64 bits.
- Python 3.10–3.12 de 64 bits recomendado para las dependencias fijadas.
- Tkinter (normalmente incluido en Python para Windows).
- Blender 5.x instalado para inspeccionar archivos \`.blend\` de la Fase 1.
- Cámara web para captura en vivo; opcional si solo probarás imágenes o vídeos.
- Internet en el primer inicio para descargar el modelo, salvo que lo proporciones manualmente.

### Instalación (PowerShell)

Desde la raíz del repositorio:

\`\`\`powershell
py -3.10 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Si Blender no está en PATH, configura la ruta real:
$env:BLENDER_EXECUTABLE = "C:\\Program Files\\Blender Foundation\\Blender 5.3\\blender.exe"
$env:PYTHONPATH = "app"
python -m genesis_mocap_tester
\`\`\`

### Probar la Fase 1

1. Abre **Fase 1 · Inspector de rigs**.
2. Selecciona tu archivo \`.blend\`.
3. Indica \`blender.exe\` si no está en PATH.
4. Pulsa **Detectar armatures** y selecciona el rig.
5. Pulsa **Validar seleccionado** para ver porcentaje, huesos encontrados y faltantes.

### Probar la Fase 2

1. Abre **Fase 2 · Motor de visión**.
2. Pulsa **Abrir imagen...** para analizar una fotografía. Si aparecen varias personas, elige la deseada en el desplegable o en la lista.
3. Pulsa **Abrir vídeo...** para cargar MP4, AVI, MOV, MKV o WEBM y luego **Iniciar / Reanudar**.
4. Para cámara, escribe su índice (normalmente \`0\`) y pulsa **Conectar cámara**; después pulsa **Iniciar / Reanudar**.
5. Ajusta **Máx. personas** antes de cargar la fuente.
6. Selecciona el modelo \`.task\` si ya lo tienes; de lo contrario se descargará en el primer inicio.
7. Activa o desactiva **Dibujar esqueleto** según necesites.
8. Selecciona una persona: su esqueleto y recuadro se resaltan en verde. El panel lateral muestra visibilidad y coordenadas de sus articulaciones.
9. Usa **Pausar** o **Detener y liberar** para terminar y liberar la cámara/modelo.

Si la cámara no abre, cierra otras aplicaciones que la usen, revisa permisos de Windows y prueba índices 0, 1 o 2. Si un vídeo no se puede leer, prueba otro códec (MP4/H.264). Para obtener mejores resultados en fotos, utiliza imágenes nítidas, con el cuerpo lo más visible posible y sin demasiada superposición entre personas.

## Pruebas automatizadas

\`\`\`powershell
python -m unittest discover -s tests -v
python -m compileall -q app tests
\`\`\`

Las pruebas de visión verifican asignación de IDs, continuidad aproximada de seguimiento, topología del esqueleto y estructura del tester para imagen/vídeo/cámara. Las pruebas de Fase 1 existentes se conservan. Las pruebas unitarias no sustituyen una prueba real con fotografías, cámara y vídeos: ejecútala desde la pestaña de visión. La Fase 1 requiere un archivo \`.blend\` real y Blender instalado.

## Estructura

\`\`\`text
app/
  genesis_mocap/                 # Addon instalable de Blender
  genesis_mocap_tester/          # Tester único de ambas fases
    blender_worker.py            # Inspección .blend dentro de Blender
    runner.py                    # Ejecuta Blender en segundo plano
    gui.py                       # Ventana con pestañas Fase 1 y Fase 2
    vision.py                    # MediaPipe IMAGE/VIDEO, multi-persona y tracking
    vision_panel.py              # Imagen/cámara/vídeo, esqueleto y selector
    __main__.py
tests/                            # Pruebas Fase 1 + Fase 2
requirements.txt
\`\`\`

## Alcance posterior

Esta fase detecta poses en imágenes y secuencias de vídeo y permite escoger un sujeto. Calibración, filtrado avanzado, conversión de landmarks a movimiento Genesis, retargeting y generación/optimización de keyframes quedan para fases posteriores.
