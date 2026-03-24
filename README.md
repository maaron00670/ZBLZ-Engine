# EN DESARROLLO
# NADA PROFESIONAL NI CON FACILIDADES DE USO, HECHO CON FINES DE APRENDER


Markdown

# ZBLZ Engine
Herramienta de Manipulación de Velocidad de Juegos en Linux - Similar a la función speedhack de Cheat Engine.

## Cómo funciona
ZBLZ Engine utiliza `LD_PRELOAD` para inyectar una librería que intercepta las llamadas al sistema relacionadas con el tiempo (`clock_gettime`, `gettimeofday`, `nanosleep`, etc.) y las modifica para acelerar o ralentizar el tiempo del juego.

### Dos modos de operación:

1. **Opciones de lanzamiento de Steam** (Actual)
   - Genera un comando y lo pegas en las propiedades del juego en Steam.
   - Funciona con cualquier juego, incluyendo juegos de Proton/Wine.
   - La velocidad se fija al momento de lanzar el juego.

2. **Adjuntar a proceso** (Futuro)
   - Adjuntarse a juegos que ya están en ejecución.
   - Cambiar la velocidad en tiempo real.

## Inicio Rápido

### 1. Compilar la librería Speedhack
```bash
cd lib/
chmod +x build.sh
./build.sh install

Esto compila libspeedhack.so e instala la librería en ~/.local/lib/zblz/.

Requisitos:

    GCC: sudo apt install build-essential

    Opcional para juegos de 32 bits: sudo apt install gcc-multilib

2. Ejecutar ZBLZ Engine
Bash

cd scripts/zblz_engine
pip install -r requirements.txt
python main.py

3. Usar con juegos de Steam

    En ZBLZ Engine, ajusta el deslizador de velocidad (por ejemplo, 2.0x para doble velocidad).

    Haz clic en "Generar Comando" para crear la opción de lanzamiento.

    En Steam: Botón derecho sobre el juego → Propiedades → Opciones de lanzamiento.

    Pega el comando generado.

    ¡Lanza el juego y se ejecutará a la velocidad modificada!

Ejemplos de comandos:

    Doble velocidad:
    LD_PRELOAD="/home/usuario/.local/lib/zblz/libspeedhack.so" SPEED=2.00 %command%

    Media velocidad (cámara lenta):
    LD_PRELOAD="/home/usuario/.local/lib/zblz/libspeedhack.so" SPEED=0.50 %command%

    Con overlay de MangoHud:
    mangohud LD_PRELOAD="/home/usuario/.local/lib/zblz/libspeedhack.so" SPEED=1.50 %command%

    Con GameMode para mejor rendimiento:
    gamemoderun LD_PRELOAD="/home/usuario/.local/lib/zblz/libspeedhack.so" SPEED=2.00 %command%

Escáner de Procesos

La lista de procesos muestra juegos de Wine/Proton/Steam en ejecución:

    Haz clic en "Actualizar" para escanear juegos en ejecución.

    Activa "Solo juegos" para ver solo procesos de juegos o todos los procesos.

    Selecciona un proceso para ver sus detalles.

    Nota: La función de adjuntar a procesos para controlar la velocidad en tiempo real está planeada para una actualización futura.

Estructura del Proyecto
Plaintext

zblz_engine/
├── main.py                    # Punto de entrada de la aplicación
├── requirements.txt           # Dependencias de Python
├── lib/
│   ├── speedhack.c            # Código fuente de la librería en C
│   ├── build.sh               # Script de compilación
│   └── libspeedhack.so        # Librería compilada (después de compilar)
├── models/
│   └── app_state.py           # Estado de la aplicación (modelo MVC)
├── views/
│   ├── main_window.py         # Ventana principal
│   ├── styles.py              # Estilos del tema oscuro
│   └── widgets/
│       ├── speed_control.py   # Widget del deslizador de velocidad
│       ├── process_list.py    # Widget del escáner de procesos
│       └── command_output.py  # Widget del generador de comandos
├── controllers/
│   └── main_controller.py     # Lógica de negocio (controlador MVC)
└── services/
    └── process_scanner.py     # Escáner del sistema de archivos /proc

Solución de Problemas
Error "Library not found"

Asegúrate de haber compilado e instalado la librería:
Bash

cd lib/
./build.sh install

El juego se cierra o no cambia de velocidad

    Algunos juegos usan métodos de temporización diferentes que pueden no ser interceptados.

    Los sistemas anti-cheat pueden bloquear LD_PRELOAD.

    Prueba tanto la versión de 32 bits como la de 64 bits para juegos antiguos.

"Permission denied" al escanear procesos

Algunos procesos requieren permisos de root para leerlos. Esto es normal en procesos del sistema.
La velocidad parece inconsistente

    Los juegos basados en física pueden tener física dependiente de la tasa de frames.

    Los juegos en línea pueden sincronizarse con el tiempo del servidor.

    Algunos juegos limitan su tasa interna de ticks.

Cómo funciona el Speedhack

La librería libspeedhack.so utiliza LD_PRELOAD para interceptar las siguientes funciones:
Función	Propósito
clock_gettime()	Función principal de temporización (CLOCK_MONOTONIC, CLOCK_REALTIME)
gettimeofday()	Función de temporización antigua
nanosleep()	Función de sleep (ajustada inversamente)
usleep()	Sleep en microsegundos
sleep()	Sleep en segundos

Fórmula de modificación del tiempo:
tiempo_modificado=tiempo_inicial+(tiempo_transcurrido×multiplicador_velocidad)

Modificación del sleep:
sleep_modificado=multiplicador_velocidadsleep_original​

Esto hace que el juego "crea" que el tiempo pasa más rápido o más lento mientras mantiene una ejecución fluida.
Funciones Futuras

    Adjuntar a procesos en tiempo real con ptrace.

    Escaneo de memoria (como Cheat Engine).

    Soporte de teclas rápidas (hotkeys) para cambiar velocidad.

    Guardar/cargar perfiles de velocidad por juego.

    Soporte completo para procesos de 32 bits.

Licencia

Licencia MIT - Gratuito para uso personal.