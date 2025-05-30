import keyboard
import mouse
import time
import logging
import random
import pyautogui
import ctypes

logger = logging.getLogger("InputService")

def press_key(key):
    pyautogui.press(key)
    logger.debug(f"Pressed key: {key}")
    return True

def mouse_down_right():
    pyautogui.mouseDown(button='right')
    logger.debug("Right mouse button down")

def mouse_up_right():
    pyautogui.mouseUp(button='right')
    logger.debug("Right mouse button up")

# Используем WinAPI для низкоуровневого движения мыши
SendInput = ctypes.windll.user32.SendInput

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001

def move_mouse_relative(dx, dy):
    mi = MouseInput(dx=dx, dy=dy, mouseData=0, dwFlags=MOUSEEVENTF_MOVE,
                    time=0, dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)))
    input_struct = Input(type=INPUT_MOUSE, ii=Input_I(mi=mi))
    SendInput(1, ctypes.pointer(input_struct), ctypes.sizeof(input_struct))
    logger.debug(f"Mouse moved relative: dx={dx}, dy={dy}")
