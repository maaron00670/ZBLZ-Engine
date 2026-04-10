# ZBLZ Engine
Herramienta para manipular la velocidad de juegos en Linux, inspirada en la función Speedhack de Cheat Engine.

Versión actual: **V 0.1.1**

## Uso para usuarios finales (sin instalar dependencias)  AUN FALTA TESTEAR

La forma recomendada para terceros es usar la versión **AppImage** publicada en Releases.

Pasos:

```bash
chmod +x ZBLZ-Engine-*.AppImage
./ZBLZ-Engine-*.AppImage
```

Con esto no necesitan instalar Python, pip ni dependencias del proyecto.

## Aviso importante
Este proyecto está hecho con fines de aprendizaje y uso personal.

El autor se apoya en IA para su desarrollo y no garantiza su funcionamiento en todos los entornos. Cualquier uso que hagas de este programa es bajo tu propia responsabilidad.

## Qué hace
ZBLZ Engine usa `LD_PRELOAD` para inyectar una librería (`libspeedhack.so`) que intercepta llamadas de tiempo del sistema, por ejemplo:

- `clock_gettime`
- `gettimeofday`
- `nanosleep`
- `usleep`
- `sleep`

Con esto, el juego percibe que el tiempo pasa más rápido o más lento.

## Modos de operación
1. **Opciones de lanzamiento de Steam (actual)**
   - Genera un comando para pegar en Steam.
   - Compatible con juegos nativos, Proton y Wine.
   - La velocidad queda fijada al iniciar el juego.

2. **Adjuntar a proceso (futuro)**
   - Permitiría engancharse a procesos ya abiertos.
   - Objetivo: cambiar la velocidad en tiempo real.

## Requisitos
- Linux
- `gcc` (compilación de la librería)
- Python 3 + `pip`
- `pynput` (hotkeys globales)
- Opcional (juegos de 32 bits): `gcc-multilib`

Instalación de dependencias base en Debian/Ubuntu:

```bash
sudo apt install build-essential
# opcional para 32 bits
sudo apt install gcc-multilib
```

## Inicio rápido
### 1. Clonar el repositorio
```bash
git clone https://github.com/maaron00670/ZBLZ-Engine
cd ZBLZ-Engine
```

### 2. Compilar e instalar la librería
```bash
cd scripts/zblz_engine/lib
chmod +x build.sh
./build.sh install
```

Esto compila `libspeedhack.so` e instala la librería en `~/.local/lib/zblz/`.

### 3. Ejecutar la aplicación
Desde la raíz del repo:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r scripts/zblz_engine/requirements.txt
python scripts/zblz_engine/main.py
```

Alternativa con `pipenv`:

```bash
cd scripts/zblz_engine
pipenv install -r requirements.txt
pipenv run python main.py
```

## Empaquetado AppImage (maintainers)
Este repositorio incluye build automático de AppImage en:

- `.github/workflows/release-appimage.yml`
- `scripts/package/build_appimage.sh`

Generación local:

```bash
chmod +x scripts/package/build_appimage.sh
scripts/package/build_appimage.sh
```

Salida esperada:

```bash
dist/ZBLZ-Engine-<version>-<arch>.AppImage
```

Publicación automática:

- Al crear un tag `v*` o un release en GitHub, el workflow compila y sube el AppImage.

## Hotkeys globales (pynput)
Para que los hotkeys funcionen en Linux:

```bash
cd /ruta/a/ZBLZ-Engine
source .venv/bin/activate
python -m pip install -r scripts/zblz_engine/requirements.txt
python -c "import pynput; print(pynput.__version__)"
```

Comprobación recomendada de sesión gráfica:

```bash
echo $XDG_SESSION_TYPE
```

- Si devuelve `x11`, los hotkeys globales deberían funcionar normalmente.
- Si devuelve `wayland`, `pynput` puede tener limitaciones para capturar teclas globales. En ese caso, prueba iniciando sesión en X11.

## Uso con Steam
1. Ajusta el deslizador de velocidad en ZBLZ Engine (por ejemplo, `2.0x`).
2. Haz clic en **Generar Comando**.
3. En Steam: clic derecho sobre el juego -> **Propiedades** -> **Opciones de lanzamiento**.
4. Pega el comando generado.
5. Inicia el juego.

## Ejemplos de comandos
```bash
# Doble velocidad
LD_PRELOAD="/home/usuario/.local/lib/zblz/libspeedhack.so${LD_PRELOAD:+:$LD_PRELOAD}" SPEED=2.00 %command%

# Media velocidad (cámara lenta)
LD_PRELOAD="/home/usuario/.local/lib/zblz/libspeedhack.so${LD_PRELOAD:+:$LD_PRELOAD}" SPEED=0.50 %command%

# Con MangoHud
mangohud LD_PRELOAD="/home/usuario/.local/lib/zblz/libspeedhack.so${LD_PRELOAD:+:$LD_PRELOAD}" SPEED=1.50 %command%

# Con GameMode
gamemoderun LD_PRELOAD="/home/usuario/.local/lib/zblz/libspeedhack.so${LD_PRELOAD:+:$LD_PRELOAD}" SPEED=2.00 %command%
```

## Escáner de procesos
La lista de procesos permite ver juegos/procesos en ejecución.

- Pulsa **Actualizar** para reescanear.
- Activa **Solo juegos** para filtrar procesos.
- Selecciona un proceso para ver detalles.

Nota: el control en tiempo real sobre procesos ya abiertos todavía no está implementado.

## Estructura del proyecto
```text
scripts/zblz_engine/
├── main.py
├── requirements.txt
├── lib/
│   ├── speedhack.c
│   ├── build.sh
│   └── libspeedhack.so
├── models/
│   └── app_state.py
├── views/
│   ├── main_window.py
│   ├── styles.py
│   └── widgets/
│       ├── speed_control.py
│       ├── process_list.py
│       └── command_output.py
├── controllers/
│   └── main_controller.py
└── services/
    └── process_scanner.py
```

## Solución de problemas
### Error: "Library not found"
Comprueba que compilaste e instalaste la librería:

```bash
cd scripts/zblz_engine/lib
./build.sh install
```

### El juego se cierra o no cambia de velocidad
- Algunos juegos usan temporizadores que no están interceptados.
- Algunos anti-cheat bloquean `LD_PRELOAD`.
- En juegos antiguos, prueba soporte 32/64 bits según corresponda.

### "Permission denied" al escanear procesos
Es normal en procesos del sistema que requieren permisos elevados.

### Velocidad inconsistente
- Algunos juegos vinculan la física a FPS.
- En juegos online, el servidor puede forzar sincronización temporal.
- Algunos motores limitan internamente sus ticks.

## Fórmula base del speedhack
- Tiempo modificado:
  `tiempo_modificado = tiempo_inicial + (tiempo_transcurrido * multiplicador_velocidad)`
- Sleep modificado (aproximación):
  `sleep_modificado = sleep_original / multiplicador_velocidad`

## Roadmap
- Adjuntar a procesos en tiempo real con `ptrace`.
- Escaneo de memoria (tipo Cheat Engine).
- Perfiles de velocidad por juego.
- Mejor soporte para procesos de 32 bits.

## Licencia
MIT. Gratis para uso personal (bajo tu propio riesgo).
