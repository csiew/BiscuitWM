import pynput

session = {
    "terminal": {
        pynput.keyboard.Key.alt,
        pynput.keyboard.KeyCode(char='x')
    },
    "window_cycle": {
        pynput.keyboard.Key.alt,
        pynput.keyboard.Key.tab
    },
    "launcher": {
        pynput.keyboard.Key.alt,
        pynput.keyboard.KeyCode(char=' ')
    },
    "exit": {
        pynput.keyboard.Key.alt,
        pynput.keyboard.KeyCode(char=' ')
    },
}

window_manipulation = {
    "close": {
        pynput.keyboard.Key.alt,
        pynput.keyboard.KeyCode(char='q')
    },
    "maximize": {
        pynput.keyboard.Key.alt,
        pynput.keyboard.KeyCode(char='=')
    },
    "move_center": {
        pynput.keyboard.Key.alt,
        pynput.keyboard.KeyCode(char='-')
    },
    "move_left": {
        pynput.keyboard.Key.alt,
        pynput.keyboard.KeyCode(char='[')
    },
    "move_right": {
        pynput.keyboard.Key.alt,
        pynput.keyboard.KeyCode(char=']')
    },
    "move_top": {
        pynput.keyboard.Key.alt,
        pynput.keyboard.KeyCode(char='\\')
    },
    "move_bottom": {
        pynput.keyboard.Key.alt,
        pynput.keyboard.KeyCode(char='/')
    },
}
