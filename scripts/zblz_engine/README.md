# ZBLZ Engine

Linux Game Speed Manipulation Tool - Similar to Cheat Engine's speedhack feature.

## How It Works

ZBLZ Engine uses `LD_PRELOAD` to inject a library that intercepts time-related system calls (`clock_gettime`, `gettimeofday`, `nanosleep`, etc.) and modifies them to speed up or slow down game time.

### Two Modes of Operation:

1. **Steam Launch Options** (Current)
   - Generate a command and paste it in Steam game properties
   - Works with any game, including Proton/Wine games
   - Speed is fixed at launch time

2. **Process Attachment** (Future)
   - Attach to already running games
   - Change speed in real-time

## Quick Start

### 1. Build the Speedhack Library

```bash
cd lib/
chmod +x build.sh
./build.sh install
```

This compiles `libspeedhack.so` and installs it to `~/.local/lib/zblz/`.

**Requirements:**
- GCC: `sudo apt install build-essential`
- Optional for 32-bit games: `sudo apt install gcc-multilib`

### 2. Run ZBLZ Engine

```bash
cd scripts/zblz_engine
pip install -r requirements.txt
python main.py
```

### 3. Use with Steam Games

1. In ZBLZ Engine, adjust the speed slider (e.g., 2.0x for double speed)
2. Click "Generate Command" to create the launch option
3. In Steam: Right-click game -> Properties -> Set Launch Options
4. Paste the generated command
5. Launch the game - it will run at modified speed!

**Example commands:**
```bash
# Double speed
LD_PRELOAD="/home/user/.local/lib/zblz/libspeedhack.so" SPEED=2.00 %command%

# Half speed (slow motion)
LD_PRELOAD="/home/user/.local/lib/zblz/libspeedhack.so" SPEED=0.50 %command%

# With MangoHud overlay
mangohud LD_PRELOAD="/home/user/.local/lib/zblz/libspeedhack.so" SPEED=1.50 %command%

# With GameMode for better performance
gamemoderun LD_PRELOAD="/home/user/.local/lib/zblz/libspeedhack.so" SPEED=2.00 %command%
```

## Process Scanner

The Process List shows running Wine/Proton/Steam games:

1. Click "Refresh" to scan for running games
2. Toggle "Games only" to see all processes or just games
3. Select a process to see details

**Note:** Process attachment for real-time speed control is planned for a future update.

## Project Structure

```
zblz_engine/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── lib/
│   ├── speedhack.c           # C library source code
│   ├── build.sh              # Build script
│   └── libspeedhack.so       # Compiled library (after build)
├── models/
│   └── app_state.py          # Application state (MVC model)
├── views/
│   ├── main_window.py        # Main window
│   ├── styles.py             # Dark theme styling
│   └── widgets/
│       ├── speed_control.py  # Speed slider widget
│       ├── process_list.py   # Process scanner widget
│       └── command_output.py # Command generator widget
├── controllers/
│   └── main_controller.py    # Business logic (MVC controller)
└── services/
    └── process_scanner.py    # /proc filesystem scanner
```

## Troubleshooting

### "Library not found" error
Make sure you've built and installed the library:
```bash
cd lib/
./build.sh install
```

### Game crashes or doesn't speed up
- Some games use different timing methods that may not be intercepted
- Anti-cheat systems may block LD_PRELOAD
- Try both 32-bit and 64-bit libraries for older games

### Permission denied when scanning processes
Some processes require root access to read. This is normal for system processes.

### Speed seems inconsistent
- Physics-based games may have frame-rate dependent physics
- Online games may sync with server time
- Some games cap their internal tick rate

## How the Speedhack Works

The `libspeedhack.so` library uses `LD_PRELOAD` to intercept these functions:

| Function | Purpose |
|----------|---------|
| `clock_gettime()` | Main timing function (CLOCK_MONOTONIC, CLOCK_REALTIME) |
| `gettimeofday()` | Legacy timing function |
| `nanosleep()` | Sleep function (adjusted inversely) |
| `usleep()` | Microsecond sleep |
| `sleep()` | Second sleep |

**Time modification formula:**
```
modified_time = initial_time + (elapsed_time * speed_multiplier)
```

**Sleep modification:**
```
modified_sleep = original_sleep / speed_multiplier
```

This makes the game "think" time passes faster/slower while maintaining smooth execution.

## Future Features

- [ ] Real-time process attachment with ptrace
- [ ] Memory scanning (like Cheat Engine)
- [ ] Hotkey support for speed toggle
- [ ] Save/load speed profiles per game
- [ ] 32-bit process support

## License

MIT License - Free for personal use
