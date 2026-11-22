# Genesis Mocap — Addon y tester integral

Herramientas para validar rigs Genesis 4C y probar el motor de visión desde una aplicación externa a Blender.

## Fase 1 — Base y validación de rigs

El addon instalable está en `app/genesis_mocap`. En Blender 5.x añade el panel **Genesis Mocap** a la Vista 3D, permite seleccionar un Armature y valida el perfil de 58 destinos: 52 huesos Genesis requeridos y 6 controles auxiliares.

El tester externo inspecciona archivos `.blend` con Blender en segundo plano, lista los objetos ARMATURE y permite validar el rig seleccionado. No instala el addon ni guarda o modifica el archivo original.

## Fase 2 — Motor de Visión

El motor está en `app/genesis_mocap_tester/vision.py` y usa MediaPipe Tasks Pose Landmarker en modo vídeo, configurado para detectar hasta el número de personas indicado (8 por defecto).

- Captura desde cámara conectada (índice configurable, normalmente 0).
- Apertura y reproducción de archivos de vídeo.
- Detección simultánea de varias poses humanas.
- Rectángulos y etiquetas dibujadas sobre cada persona.
- Lista y selector para escoger el sujeto objetivo; queda resaltado en verde.
- Seguimiento temporal aproximado por proximidad del centro del cuerpo entre fotogramas.

**Importante:** los números de persona son IDs temporales de seguimiento, no reconocimiento de identidad. Si alguien sale del encuadre, queda oculto o cruza con otra persona, el ID puede cambiar. Esta fase no genera animaciones, keyframes ni retargeting.

### Modelo de visión

Se usa el modelo ligero oficial `pose_landmarker_lite.task`. En el primer inicio se descarga automáticamente si no existe. Se guarda en:

- Windows: `%LOCALAPPDATA%\GenesisMocap\models\pose_landmarker_lite.task`
- Otros sistemas: `~/GenesisMocap/models/pose_landmarker_lite.task`

También puedes seleccionar un archivo `.task` local desde el tester. La descarga automática requiere Internet en el primer inicio.

## Tester integral (Fase 1 + Fase 2)

Las dos fases se prueban desde una sola aplicación y carpeta: `app/genesis_mocap_tester`.

### Requisitos

- Windows 10/11 de 64 bits.
- Python 3.10–3.12 de 64 bits recomendado para las dependencias fijadas.
- Tkinter (normalmente incluido en Python para Windows).
- Blender 5.x instalado para inspeccionar archivos `.blend` de la Fase 1.
- Cámara web para captura en vivo; opcional si solo probarás vídeos.
- Internet en el primer inicio para descargar el modelo, salvo que lo proporciones manualmente.

### Instalación (PowerShell)

Desde la raíz del repositorio:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Si Blender no está en PATH, configura la ruta real:
$env:BLENDER_EXECUTABLE = "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"
$env:PYTHONPATH = "app"
python -m genesis_mocap_tester
```

### Probar la Fase 1

1. Abre **Fase 1 · Inspector de rigs**.
2. Selecciona tu archivo `.blend`.
3. Indica `blender.exe` si no está en PATH.
4. Pulsa **Detectar armatures** y selecciona el rig.
5. Pulsa **Validar seleccionado** para ver porcentaje, huesos encontrados y faltantes.

### Probar la Fase 2

1. Abre **Fase 2 · Motor de visión**.
2. Para un vídeo, pulsa **Abrir vídeo...** y selecciona MP4, AVI, MOV u otro formato compatible con OpenCV.
3. Para cámara, escribe su índice (normalmente `0`) y pulsa **Conectar cámara**.
4. Ajusta **Máx. personas** antes de iniciar.
5. Selecciona el modelo `.task` si ya lo tienes; de lo contrario se descargará en el primer inicio.
6. Pulsa **Iniciar / Reanudar**. Verás rectángulos y etiquetas sobre las personas detectadas.
7. Elige el sujeto en la lista o el desplegable; se resalta en verde.
8. Usa **Pausar** o **Detener y liberar** para terminar y liberar la cámara/modelo.

Si la cámara no abre, cierra otras aplicaciones que la usen, revisa permisos de Windows y prueba índices 0, 1 o 2. Si un vídeo no se puede leer, prueba otro códec (MP4/H.264).

## Pruebas automatizadas

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app tests
```

Las pruebas de visión verifican asignación de IDs, continuidad aproximada de seguimiento, detecciones separadas y estructura del tester integral. Las pruebas de Fase 1 existentes se conservan. Las pruebas unitarias no sustituyen una prueba real de cámara/vídeo: ejecútala desde la pestaña de visión. La Fase 1 requiere un archivo `.blend` real y Blender instalado.

## Estructura

```text
app/
  genesis_mocap/                 # Addon instalable de Blender
  genesis_mocap_tester/           # Tester único de ambas fases
    blender_worker.py             # Inspección .blend dentro de Blender
    runner.py                     # Ejecuta Blender en segundo plano
    gui.py                        # Ventana con pestañas Fase 1 y Fase 2
    vision.py                     # MediaPipe multi-persona y tracking
    vision_panel.py               # Cámara/vídeo, preview y selector visual
    __main__.py
tests/                            # Pruebas Fase 1 + Fase 2
requirements.txt
```

## Alcance posterior

La Fase 2 detecta poses y permite escoger un sujeto. Calibración, filtrado avanzado, conversión de landmarks a movimiento Genesis, retargeting y generación/optimización de keyframes quedan para fases posteriores.
