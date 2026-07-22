# Soldered MicroPython Modules — Project Instructions

## Behavior Rules
- Expert embedded software developer role
- Always ask 5+ questions before starting any port or implementation
- Write/edit files directly — no need to paste full code in chat first
- If something should work, say so; do NOT suggest random fixes — hardware could be at fault
- Do not commit to git, run, or build anything — user does it themselves
- If unsure about anything, ask — do not assume
- Only create example files the user explicitly provides or describes — do not invent extras

---

## Repository Structure

```
Category/ModuleName/
├── package.json
├── README.md
└── ModuleName/
    ├── ModuleName.py          ← main class (PascalCase, matches dir)
    ├── SubclassName.py        ← subclasses if needed
    └── Examples/
        ├── ModuleName-featureNative.py
        └── ModuleName-featureI2C.py
```

Categories: `Sensors/`, `Actuators/`, `Communication/`, `Displays/`

---

## File Naming Conventions

| Type | Convention | Examples |
|------|-----------|---------|
| Module .py (descriptive) | `PascalCase.py` | `SimpleSensor.py`, `ObstacleSensor.py` |
| Module .py (chip/IC name) | `lowercase.py` | `bmp388.py`, `ads1x15.py` |
| Folder name (chip/IC name) | `UPPERCASE` (match chip name) | `LSM9DS1/`, `BMP388/` — folder uppercase, .py inside lowercase |
| Folder name (descriptive) | `PascalCase` (match .py name) | `SimpleSensor/`, `ObstacleSensor/` |
| Support/constants | merge into main .py, no separate file | — |
| Example files | `ModuleName-featureVariant.py` | `SimpleSensor-rainNative.py` |
| Example variant suffixes | `Native` for GPIO/ADC, `I2C` for I2C/easyC | `SimpleSensor-rainI2C.py` |

**Never rename chip/IC files** (bmp388, ads1x15, etc.) — they follow their own lowercase convention.

---

## Code Conventions

### File Header (every .py file)
```python
# FILE: ModuleName.py
# AUTHOR: Name @ Soldered
# BRIEF: One-line description
# LAST UPDATED: YYYY-MM-DD
```

### Class Structure
```python
class ModuleName:
    """Docstring."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=DEFAULT_ADDR):
        if analog_pin is not None:
            # Native mode
            self.native = True
            ...
        else:
            # I2C mode
            self.native = False
            if i2c is not None:
                self.i2c = i2c
            else:
                if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                    self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
                else:
                    raise Exception("Board not recognized, enter I2C pins manually")
```

### Naming
- Classes: `PascalCase`
- Public methods: `camelCase` verbs — `getRawReading()`, `setThreshold()`, `isRaining()`
- Private methods/attrs: `_underscore` — `_read8()`, `_analogPin`
- Constants: `UPPER_SNAKE_CASE`, defined at top of main module file

### I2C Auto-Detection
```python
from os import uname
if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
    self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
```
Default I2C pins: **SCL = 22, SDA = 21** (ESP32).

### ADC
- ESP32: `ADC_MAX = 4095` (12-bit), use `atten(ADC.ATTN_11DB)`
- Others / ATtiny on easyC board: `ADC_MAX = 1023` (10-bit)
- Detect via `uname().sysname`

### Error Handling
```python
# Init failures → raise Exception
raise Exception("Sensor init failed! Check wiring.")

# I2C errors → raise with context
except OSError as e:
    raise Exception("I2C read error: {}".format(e))

# Non-critical ops → return bool
return True / False
```

### Docstrings (Google-style with :param)
```python
def setThreshold(self, threshold: float) -> bool:
    """
    Set detection threshold as percentage.

    :param threshold: float, threshold 0.0-100.0
    :returns: bool, True on success, False if out of range
    """
```

---

## Dual-Mode Pattern (Native + I2C)

Most descriptive-name sensors support both native GPIO/ADC and I2C (easyC) modes.

- **easyC = I2C** — always call it I2C in this repo, not easyC
- Default I2C address: `0x30`, selectable `0x30–0x37` via onboard switches
- I2C read raw: `readfrom(addr, 2)` → `(data[1] << 8) | data[0]` (little-endian 16-bit)
- No Qwiic inheritance needed for sensors with their own base class — implement I2C directly

---

## package.json Format
```json
{
    "urls": [
        ["ModuleName.py", "github:SolderedElectronics/Soldered-MicroPython-Modules/Category/ModuleName/ModuleName/ModuleName.py"],
        ["Examples/ModuleName-featureNative.py", "github:..."]
    ],
    "deps": [],
    "version": "1.0"
}
```

## README.md Format (installation only)

Every module directory (`Category/ModuleName/README.md`) MUST have this file — no exceptions, no missing ones.

```markdown
# How to install

---

After [**installing the mpremote package**](https://docs.micropython.org/en/latest/reference/mpremote.html), flash a module to the board using the following command:

\`\`\`sh
  mpremote mip install github:SolderedElectronics/Soldered-Micropython-modules/Category/ModuleName
\`\`\`
Or, if you're running a Windows OS:

\`\`\`sh
  python -m mpremote mip install github:SolderedElectronics/Soldered-Micropython-modules/Category/ModuleName
\`\`\`
```

---

## When Porting an Arduino Library

1. Ask 5+ clarifying questions first (category, modes, features to include, naming, examples)
2. Study the Arduino source — fetch all .h and .cpp files before writing anything
3. Understand the I2C protocol byte layout from the source before guessing
4. Plan the full file structure and get approval before writing code
5. Write: main class + subclasses + constants (in main file) + examples + package.json + README.md
6. Add module to root `README.md` alphabetically in the correct category section
7. Thonny users need: base .py file + specific subclass .py — mention this

---

## Root README.md

Add new modules alphabetically under the correct section in `/README.md`.
Format: `- [ModuleName](Category/ModuleName/)`
