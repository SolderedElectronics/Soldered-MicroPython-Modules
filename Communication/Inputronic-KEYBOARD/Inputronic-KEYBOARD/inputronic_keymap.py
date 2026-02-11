# FILE: inputronic_keymap.py
# AUTHOR: Marko Toldi @ Soldered
# BRIEF: Default keymaps for Soldered Inputronic Keyboard (8x10)
# LAST UPDATED: 2026-02-11

# Each keymap is [8][10], row-major: keymap[row][col]
# Use None for unmapped positions.

INPUTRONIC_KEYMAP_UPPER = [
    # Row 0
    [None, None, None, None, None, None, "UP", "LEFT", "DOWN", "RIGHT"],
    # Row 1
    [None, None, None, "BACK", "ENTER", "DEL", "FN3", "FN4", "FN5", "FN6"],
    # Row 2
    ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"],
    # Row 3
    ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    # Row 4
    ["P", "Q", "W", "E", "R", "T", "Y", "U", "I", "O"],
    # Row 5
    [";", "A", "S", "D", "F", "G", "H", "J", "K", "L"],
    # Row 6
    [None, "Z", "X", "C", "V", "B", "N", "M", ",", "."],
    # Row 7
    [None, "ESC", "TAB", "CAPS", "SHIFT", "CTRL", "ALT", "FN1", "FN2", "SPACE"],
]

INPUTRONIC_KEYMAP_LOWER = [
    # Row 0
    [None, None, None, None, None, None, "UP", "LEFT", "DOWN", "RIGHT"],
    # Row 1
    [None, None, None, "BACK", "ENTER", "DEL", "FN3", "FN4", "FN5", "FN6"],
    # Row 2
    ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"],
    # Row 3
    ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    # Row 4
    ["p", "q", "w", "e", "r", "t", "y", "u", "i", "o"],
    # Row 5
    [";", "a", "s", "d", "f", "g", "h", "j", "k", "l"],
    # Row 6
    [None, "z", "x", "c", "v", "b", "n", "m", ",", "."],
    # Row 7
    [None, "ESC", "TAB", "CAPS", "SHIFT", "CTRL", "ALT", "FN1", "FN2", "SPACE"],
]
