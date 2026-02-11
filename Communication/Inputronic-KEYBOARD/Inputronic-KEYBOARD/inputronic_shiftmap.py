# FILE: inputronic_shiftmap.py
# AUTHOR: (port) ChatGPT based on Soldered Arduino library
# BRIEF: SHIFT character mapping for Soldered Inputronic Keyboard
# LAST UPDATED: 2026-02-11

# Base char -> shifted char
INPUTRONIC_SHIFT_MAP = {
    "1": "!",
    "2": '"',
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "&",
    "7": "/",
    "8": "(",
    "9": ")",
    "0": "=",
    ";": ":",
    ",": ";",
    ".": ":",
    # If you want typical PC style:
    # ".": ">",
}

def inputronic_apply_shift(ch: str):
    """
    Apply shift mapping to a single-character string.
    Returns shifted char (str len=1) or None if no mapping exists.
    """
    if not ch or len(ch) != 1:
        return None
    return INPUTRONIC_SHIFT_MAP.get(ch, None)