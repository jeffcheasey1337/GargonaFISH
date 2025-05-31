import keyboard
import mouse
import time
import logging
import random
import pyautogui
import pydirectinput
import math

logger = logging.getLogger("InputService")


def press_key(key):
    pyautogui.press(key)
    logger.debug(f"Pressed key: {key}")
    return True


def mouse_down_right():
    pydirectinput.mouseDown(button='right')
    logger.debug("Right mouse button down")


def mouse_up_right():
    pydirectinput.mouseUp(button='right')
    logger.debug("Right mouse button up")


def move_mouse_relative(dx, dy):
    """
    Используем pydirectinput для относительного движения мыши.
    """
    pydirectinput.moveRel(dx, dy)
    logger.debug(f"Mouse moved relative: dx={dx}, dy={dy}")


def move_towards(target, max_step=25):
    """
    Двигает курсор к указанной точке target (x, y), пошагово, используя move_mouse_relative.
    Возвращает True, если достигнута цель.
    """
    current_x, current_y = pyautogui.position()
    target_x, target_y = target
    dx = target_x - current_x
    dy = target_y - current_y
    distance = math.hypot(dx, dy)

    if distance < 1:
        logger.debug("Cursor already at target.")
        return True

    scale = min(max_step / distance, 1.0)
    step_dx = int(dx * scale)
    step_dy = int(dy * scale)

    if step_dx == 0 and dx != 0:
        step_dx = 1 if dx > 0 else -1
    if step_dy == 0 and dy != 0:
        step_dy = 1 if dy > 0 else -1

    move_mouse_relative(step_dx, step_dy)
    logger.debug(f"Moving towards: {target}, step=({step_dx}, {step_dy})")

    return False
