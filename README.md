# Qué es ZBLZ-Engine
ZBLZ-Engine es un proyecto cuya finalidad es ser una alternativa de Cheat Engine pero para Linux.
Este proyecto irá escalando de poco en poco, empezando con alguna función simple y ya avanzando.
Por ahora la intención es crear una GUI en la que puedas elegir el proceso y poder usar la función speedhack de Cheat Engine.

# ZBLZ Engine
Una aplicación de escritorio para Linux destinada al análisis de procesos y manipulación de velocidad, similar a Cheat Engine.

## Características
* **Control de Velocidad:** Genera opciones de lanzamiento de Steam con multiplicadores de velocidad personalizados (0.1x - 5.0x).
* **Lista de Procesos:** Visualiza los procesos en ejecución (preparado para futuras funciones de acoplamiento).
* **Copiar al Portapapeles:** Copia fácilmente los comandos de lanzamiento generados.
* **Tema Oscuro:** Interfaz de usuario moderna y limpia.

## Requisitos
* Python 3.8+
* PyQt5
* Linux (Debian/Ubuntu/Arch)

## Instalación
```bash
# Clonar o descargar el proyecto
cd zblz_engine

# Crear un entorno virtual (opcional pero recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Ejecución
```bash
python main.py
```

## Uso
1. Ajusta el multiplicador de velocidad usando el deslizador o los botones preestablecidos.
2. Configura la ruta de la librería speedhack (por defecto: `/usr/lib/zblz/speedhack.so`).
3. Opcionalmente, activa MangoHud o GameMode.
4. Haz clic en "Generar opción de lanzamiento de Steam".
5. Copia el comando y pégalo en las propiedades del juego en Steam.

## Estructura del Proyecto
```text
zblz_engine/
├── main.py                 # Punto de entrada de la aplicación
├── requirements.txt        # Dependencias de Python
├── README.md              # Este archivo
│
├── models/                 # Modelos de datos (MVC - Modelo)
│   ├── __init__.py
│   └── app_state.py       # Gestión del estado de la aplicación
│
├── views/                  # Componentes de la IU (MVC - Vista)
│   ├── __init__.py
│   ├── main_window.py     # Ventana principal de la aplicación
│   ├── styles.py          # Estilo del tema oscuro
│   └── widgets/           # Widgets de IU reutilizables
│       ├── __init__.py
│       ├── speed_control.py
│       ├── process_list.py
│       └── command_output.py
│
└── controllers/            # Lógica de negocio (MVC - Controlador)
    ├── __init__.py
    └── main_controller.py # Controlador principal
```

## Arquitectura
La aplicación sigue el patrón MVC (Modelo-Vista-Controlador):

* **Modelo (models/app_state.py):** Gestiona el estado de la aplicación utilizando el patrón observer.
* **Vista (views/):** Widgets de PyQt5 para el renderizado de la interfaz.
* **Controlador (controllers/):** Lógica de negocio y coordinación.

## Extendiendo la Aplicación

### Añadir una Nueva Función
1. **Añade el estado al modelo (models/app_state.py):**
```python
# Añade propiedades y métodos para tu función
@property
def my_feature_state(self):
    return self._my_feature_state
```

2. **Crea un widget (views/widgets/my_feature.py):**
```python
class MyFeatureWidget(QWidget):
    # Define señales para las interacciones del usuario
    action_requested = pyqtSignal()
```

3. **Añade la lógica al controlador (controllers/main_controller.py):**
```python
def handle_my_feature(self):
    # Lógica de negocio aquí
    pass
```

4. **Integra en la ventana principal (views/main_window.py):**
* Añade el widget al diseño (layout).
* Conecta las señales al controlador.

### Añadir Escaneo de Memoria (Futuro)
* Crear `models/memory_state.py` para los resultados del escaneo.
* Crear `views/widgets/memory_scanner.py` para la interfaz.
* Crear `controllers/memory_controller.py` para la lógica de ptrace.
* Integrar en la pestaña del Escáner de Memoria.

### Añadir Acoplamiento de Procesos (Futuro)
* Crear un servicio backend utilizando llamadas al sistema ptrace.
* Añadir el estado de acoplamiento a `AppState`.
* Habilitar el control de velocidad en tiempo real mediante manipulación de memoria.

## Librería Speedhack
La funcionalidad de speedhack requiere una librería en C separada (`speedhack.so`) que intercepte (hook) las funciones de tiempo. Esta librería debería:

1. Interceptar `gettimeofday`, `clock_gettime`, `time`.
2. Leer la variable de entorno `SPEED`.
3. Escalar los valores de tiempo en consecuencia.

Ejemplo de estructura de implementación:

```c
// speedhack.c
#define _GNU_SOURCE
#include <dlfcn.h>
#include <time.h>
#include <stdlib.h>

static double speed_factor = 1.0;

__attribute__((constructor))
void init() {
    char* speed_env = getenv("SPEED");
    if (speed_env) speed_factor = atof(speed_env);
}

// Interceptar funciones de tiempo y escalar por speed_factor
```

Compilar con:
```bash
gcc -shared -fPIC -o speedhack.so speedhack.c -ldl
```

## Licencia
Licencia MIT

---
