import pyautogui
import random
import time

pyautogui.FAILSAFE = False

def move_cursor_towards(from_pos, to_pos, steps=30, delay_range=(0.01, 0.03), jitter=3):
    fx, fy = from_pos
    tx, ty = to_pos
    screenWidth, screenHeight = pyautogui.size()

    dx = (tx - fx) / steps
    dy = (ty - fy) / steps

    current_x, current_y = fx, fy
    for _ in range(steps):
        jitter_x = random.uniform(-jitter, jitter)
        jitter_y = random.uniform(-jitter, jitter)

        new_x = int(min(max(0, current_x + dx + jitter_x), screenWidth - 1))
        new_y = int(min(max(0, current_y + dy + jitter_y), screenHeight - 1))

        pyautogui.moveTo(new_x, new_y, duration=0)
        current_x, current_y = new_x, new_y

        delay = random.uniform(*delay_range)
        time.sleep(delay)
