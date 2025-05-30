import time
import pyautogui
import numpy as np
from PIL import ImageGrab
import os
import logging
from datetime import datetime
import cv2

from services.config_reader import read_binded_key
from services.utils import get_stop_flag
from core.template_matching import find_all_templates, find_template_with_mask, get_template_center, distance_points
from core.movement import move_cursor_towards

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(ROOT_DIR, "templates")

SPLASH_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "splash.png")
CIRCLE_NAV_TEMPLATE  = os.path.join(TEMPLATE_DIR, "circle_nav.png")
CIRCLE_GAME_TEMPLATE = os.path.join(TEMPLATE_DIR, "circle_game.png")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

INITIAL_CIRCLE_POS = (1173, 576)

def start_fishing(key=None):
    if not key:
        key = read_binded_key()
    if not key:
        logging.error("Не найдена клавиша для заброса удочки.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshots_dir = os.path.join(ROOT_DIR, f"screenshots_{timestamp}")
    os.makedirs(screenshots_dir, exist_ok=True)
    logging.info(f"Папка для скриншотов: {screenshots_dir}")

    screenshot = np.array(ImageGrab.grab())
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    splash_positions_vals = find_all_templates(screenshot, SPLASH_TEMPLATE_PATH, threshold=0.7)
    if not splash_positions_vals:
        logging.warning("Всплески не найдены, рыбалка не начата.")
        return

    closest_splash = min(splash_positions_vals,
                         key=lambda x: distance_points(INITIAL_CIRCLE_POS, get_template_center(x[0], SPLASH_TEMPLATE_PATH)))
    splash_pos, splash_val = closest_splash
    splash_center = get_template_center(splash_pos, SPLASH_TEMPLATE_PATH)
    logging.info(f"Ближайший всплеск найден в {splash_center} с вероятностью {splash_val:.3f}")

    pyautogui.press(key)
    time.sleep(1)
    logging.info("Удочка взята, нажимаем ПКМ...")
    pyautogui.mouseDown(button='right')

    circle_pos = INITIAL_CIRCLE_POS
    circle_center = circle_pos

    try:
        logging.info(f"Ведём круг наведения из {circle_center} к всплеску {splash_center}")
        move_cursor_towards(circle_center, splash_center)

        while not get_stop_flag():
            screenshot = np.array(ImageGrab.grab())
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

            splash_positions_vals = find_all_templates(screenshot, SPLASH_TEMPLATE_PATH, threshold=0.7)
            circle_pos, circle_val = find_template_with_mask(screenshot, CIRCLE_NAV_TEMPLATE, threshold=0.75)

            if not splash_positions_vals:
                logging.info("Всплесков не обнаружено. Рыбалка завершена.")
                break
            if circle_pos is None:
                logging.warning("Круг навигации не найден. Пропускаем цикл.")
                time.sleep(0.1)
                continue

            circle_center = get_template_center(circle_pos, CIRCLE_NAV_TEMPLATE)
            max_splash_y = max(get_template_center(pos, SPLASH_TEMPLATE_PATH)[1] for pos, _ in splash_positions_vals)
            if circle_center[1] < max_splash_y:
                logging.info("Круг навигации ушел выше всех всплесков, отпускаем ПКМ и берем заново.")
                pyautogui.mouseUp(button='right')
                time.sleep(0.2)
                pyautogui.mouseDown(button='right')
                screenshot = np.array(ImageGrab.grab())
                screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
                circle_pos, circle_val = find_template_with_mask(screenshot, CIRCLE_NAV_TEMPLATE, threshold=0.75)
                if circle_pos is None:
                    logging.warning("После перехвата круг навигации не найден. Пропускаем цикл.")
                    time.sleep(0.1)
                    continue
                circle_center = get_template_center(circle_pos, CIRCLE_NAV_TEMPLATE)

            closest_splash = min(splash_positions_vals,
                                 key=lambda x: distance_points(circle_center, get_template_center(x[0], SPLASH_TEMPLATE_PATH)))
            splash_pos, splash_val = closest_splash
            splash_center = get_template_center(splash_pos, SPLASH_TEMPLATE_PATH)

            logging.info(f"Наводимся на всплеск {splash_center} с вероятностью {splash_val:.3f}")
            move_cursor_towards(circle_center, splash_center)
            circle_center = splash_center

            logging.info("Ждём мини-игру после наведения...")
            wait_for_catch(splash_center)

            time.sleep(0.05)

    finally:
        pyautogui.mouseUp(button='right')
        logging.info("ПКМ отпущена.")


def wait_for_catch(target_center, timeout=6):
    import cv2
    logging.info("Ждём совпадения сужающегося круга...")
    start = time.time()
    while time.time() - start < timeout:
        if get_stop_flag():
            return

        screenshot = np.array(ImageGrab.grab())
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

        pos, val = find_template_with_mask(screenshot, CIRCLE_GAME_TEMPLATE, threshold=0.85)
        if pos:
            circle_center = get_template_center(pos, CIRCLE_GAME_TEMPLATE)
            dist = ((circle_center[0] - target_center[0]) ** 2 + (circle_center[1] - target_center[1]) ** 2) ** 0.5
            if dist < 10:
                pyautogui.press('space')
                logging.info("Улов пойман!")
                break

        time.sleep(0.05)
