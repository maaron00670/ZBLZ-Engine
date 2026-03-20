# ZBLZ Engine

A Linux desktop application for process analysis and speed manipulation, similar to Cheat Engine.

## Features

- **Speed Control**: Generate Steam launch options with custom speed multipliers (0.1x - 5.0x)
- **Process List**: View running processes (prepared for future attachment features)
- **Copy to Clipboard**: Easy copy of generated launch commands
- **Dark Theme**: Modern, clean UI

## Requirements

- Python 3.8+
- PyQt5
- Linux (Debian/Ubuntu/Arch)

## Installation

```bash
# Clone or download the project
cd zblz_engine

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## Usage

1. Adjust the speed multiplier using the slider or preset buttons
2. Configure the speedhack library path (default: `/usr/lib/zblz/speedhack.so`)
3. Optionally enable MangoHud or GameMode
4. Click "Generate Steam Launch Option"
5. Copy the command and paste it into Steam game properties

## Project Structure

```
zblz_engine/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── models/                 # Data models (MVC - Model)
│   ├── __init__.py
│   └── app_state.py       # Application state management
│
├── views/                  # UI components (MVC - View)
│   ├── __init__.py
│   ├── main_window.py     # Main application window
│   ├── styles.py          # Dark theme styling
│   └── widgets/           # Reusable UI widgets
│       ├── __init__.py
│       ├── speed_control.py
│       ├── process_list.py
│       └── command_output.py
│
└── controllers/            # Business logic (MVC - Controller)
    ├── __init__.py
    └── main_controller.py # Main controller
```

## Architecture

The application follows the MVC (Model-View-Controller) pattern:

- **Model** (`models/app_state.py`): Manages application state using observer pattern
- **View** (`views/`): PyQt5 widgets for UI rendering
- **Controller** (`controllers/`): Business logic and coordination

## Extending the Application

### Adding a New Feature

1. **Add state to the model** (`models/app_state.py`):
   ```python
   # Add properties and methods for your feature
   @property
   def my_feature_state(self):
       return self._my_feature_state
   ```

2. **Create a widget** (`views/widgets/my_feature.py`):
   ```python
   class MyFeatureWidget(QWidget):
       # Define signals for user interactions
       action_requested = pyqtSignal()
   ```

3. **Add controller logic** (`controllers/main_controller.py`):
   ```python
   def handle_my_feature(self):
       # Business logic here
       pass
   ```

4. **Integrate into main window** (`views/main_window.py`):
   ```python
   # Add widget to layout
   # Connect signals to controller
   ```

### Adding Memory Scanning (Future)

1. Create `models/memory_state.py` for scan results
2. Create `views/widgets/memory_scanner.py` for UI
3. Create `controllers/memory_controller.py` for ptrace logic
4. Integrate into the Memory Scanner tab

### Adding Process Attachment (Future)

1. Create backend service using `ptrace` system calls
2. Add attachment state to `AppState`
3. Enable real-time speed control via memory manipulation

## Speedhack Library

The speedhack functionality requires a separate C library (`speedhack.so`) that hooks time functions. This library should:

- Hook `gettimeofday`, `clock_gettime`, `time`
- Read `SPEED` environment variable
- Scale time values accordingly

Example implementation structure:
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

// Hook time functions and scale by speed_factor
```

Compile with:
```bash
gcc -shared -fPIC -o speedhack.so speedhack.c -ldl
```

## License

MIT License
