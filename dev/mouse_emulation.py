import time
import pyautogui
import ctypes
import pydirectinput

# --- WinAPI ctypes для движения мыши ---
SendInput = ctypes.windll.user32.SendInput

class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

class Input(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ii", Input_I)
    ]

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

def winapi_send(input_struct):
    SendInput(1, ctypes.pointer(input_struct), ctypes.sizeof(input_struct))

# --- Зажать ПКМ один раз в начале ---
def hold_right_mouse_button():
    mi_down = MouseInput(dx=0, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_RIGHTDOWN,
                         time=0, dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)))
    input_down = Input(type=INPUT_MOUSE, ii=Input_I(mi=mi_down))
    winapi_send(input_down)
    print("[WinAPI] ПКМ зажата")

def release_right_mouse_button():
    mi_up = MouseInput(dx=0, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_RIGHTUP,
                       time=0, dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)))
    input_up = Input(type=INPUT_MOUSE, ii=Input_I(mi=mi_up))
    winapi_send(input_up)
    print("[WinAPI] ПКМ отпущена")

# --- Функции движения мыши вправо по разному ---

def pyautogui_move_right(duration=5):
    end_time = time.time() + duration
    while time.time() < end_time:
        pyautogui.moveRel(10, 0)
        time.sleep(0.05)

def winapi_move_right(duration=5):
    end_time = time.time() + duration
    while time.time() < end_time:
        mi_move = MouseInput(dx=10, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_MOVE,
                             time=0, dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)))
        input_move = Input(type=INPUT_MOUSE, ii=Input_I(mi=mi_move))
        winapi_send(input_move)
        time.sleep(0.05)

def pydirectinput_move_right(duration=5):
    end_time = time.time() + duration
    while time.time() < end_time:
        pydirectinput.moveRel(10, 0)
        time.sleep(0.05)

# --- Основная логика цикла ---

def main():
    print("Старт через 5 секунд. Приготовься...")
    time.sleep(5)

    hold_right_mouse_button()

    funcs = [
        ("pyautogui_move_right", pyautogui_move_right),
        ("winapi_move_right", winapi_move_right),
        ("pydirectinput_move_right", pydirectinput_move_right),
    ]

    try:
        while True:
            for name, func in funcs:
                print(f"\nЗапуск функции: {name}")
                func(duration=5)
                time.sleep(1)  # небольшой перерыв между функциями
    except KeyboardInterrupt:
        print("\nОстановка скрипта...")
    finally:
        release_right_mouse_button()

if __name__ == "__main__":
    main()
