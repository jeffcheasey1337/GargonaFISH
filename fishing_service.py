import time
import logging
import keyboard
import pyautogui
from input_service import press_key, move_mouse_relative, mouse_down_right, mouse_up_right, move_towards
from config_service import load_config
import cv2
import numpy as np
import os
import math
from datetime import datetime

logger = logging.getLogger("FishingService")


class FishingManager:
    def __init__(self):
        self.running = False
        self.paused = False
        self.config = load_config()
        self.move_mode = 'splash'  # splash, left, right
        logger.info("Fishing manager initialized")

    def toggle_pause(self):
        self.paused = not self.paused
        logger.info("Fishing paused" if self.paused else "Fishing resumed")

    def set_move_mode(self, mode):
        if mode in ('splash', 'left', 'right'):
            self.move_mode = mode
            logger.info(f"Move mode set to: {mode}")
        else:
            logger.warning(f"Invalid move mode attempted to set: {mode}")

    def find_splashes(self):
        template_path = os.path.join("templates", "splash.png")
        if not os.path.exists(template_path):
            logger.error(f"Template splash.png not found at {template_path}")
            return [], 0, 0

        screenshot = pyautogui.screenshot()
        screenshot_rgb = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_rgb, cv2.COLOR_RGB2GRAY)

        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            logger.error("Failed to load splash template image")
            return [], 0, 0

        w, h = template.shape[1], template.shape[0]
        res = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.9
        loc = np.where(res >= threshold)

        points = []
        for pt in zip(*loc[::-1]):
            center_x = pt[0] + w // 2
            center_y = pt[1] + h // 2
            points.append((center_x, center_y))

        filtered_points = []
        for p in points:
            if all(np.linalg.norm(np.array(p) - np.array(fp)) > 50 for fp in filtered_points):
                filtered_points.append(p)

        logger.debug(f"Found {len(filtered_points)} splashes by template matching")
        return filtered_points, w, h

    def make_debug_screenshot(self, path, splashes, splash_size, highlight_point=None):
        screenshot = pyautogui.screenshot()
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        mouse_pos = pyautogui.position()
        cv2.circle(img, mouse_pos, 15, (0, 255, 0), 3)

        w, h = splash_size
        for (x, y) in splashes:
            top_left = (int(x - w / 2), int(y - h / 2))
            bottom_right = (int(x + w / 2), int(y + h / 2))
            cv2.rectangle(img, top_left, bottom_right, (255, 0, 0), 2)

        if highlight_point is not None:
            x, y = highlight_point
            top_left = (int(x - w / 2), int(y - h / 2))
            bottom_right = (int(x + w / 2), int(y + h / 2))
            cv2.rectangle(img, top_left, bottom_right, (0, 0, 255), 3)

        cv2.imwrite(path, img)

    def start_fishing(self):
        if self.running:
            logger.warning("Fishing already running")
            return

        self.running = True
        self.paused = False
        self.config = load_config()
        pause_key = self.config.get("pause_key", "p")
        exit_key = self.config.get("exit_key", "q")

        keyboard.on_press_key(exit_key, lambda _: self.force_exit())
        keyboard.on_press_key(pause_key, lambda _: self.toggle_pause())

        try:
            session_dir = os.path.join("debug_screenshots", datetime.now().strftime("%Y%m%d_%H%M%S"))
            os.makedirs(session_dir, exist_ok=True)

            logger.info("Waiting 5 seconds before casting")
            time.sleep(5)

            if not press_key(self.config['bind_key']):
                logger.error("Failed to activate fishing rod")
                self.running = False
                return

            logger.info("Waiting 2 seconds after casting")
            time.sleep(2)

            logger.info("Holding right mouse button down")
            mouse_down_right()
            time.sleep(0.1)

            self.make_debug_screenshot(os.path.join(session_dir, "step_0_after_cast.png"), [], (0, 0))

            speed = self.config.get('speed', 5)
            max_step = 20 * speed

            step_num = 1
            target = None
            w = h = 0

            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue

                if self.move_mode == 'splash':
                    if target is None:
                        splashes, w, h = self.find_splashes()
                        if not splashes:
                            logger.info("No splashes found, waiting...")
                            time.sleep(0.1)
                            continue

                        current_pos = pyautogui.position()
                        target = min(
                            splashes,
                            key=lambda p: (p[0] - current_pos[0]) ** 2 + (p[1] - current_pos[1]) ** 2
                        )
                        logger.info(f"New target splash at {target}")

                    reached = move_towards(target, max_step)

                    splashes, _, _ = self.find_splashes()
                    debug_path = os.path.join(session_dir, f"step_{step_num}_move.png")
                    self.make_debug_screenshot(debug_path, splashes, (w, h), highlight_point=target)
                    step_num += 1

                    time.sleep(0.05)

                    if reached:
                        logger.info("Reached splash target")
                        target = None
                        continue

                else:
                    current_pos = pyautogui.position()
                    step_dx = max_step if self.move_mode == 'right' else -max_step
                    step_dy = 0

                    move_mouse_relative(step_dx, step_dy)
                    new_pos = pyautogui.position()
                    logger.info(f"Moved mouse {self.move_mode} by relative ({step_dx}, {step_dy}), new pos: {new_pos}")

                    debug_path = os.path.join(session_dir, f"step_{step_num}_move_direction.png")
                    self.make_debug_screenshot(debug_path, [], (0, 0))
                    step_num += 1

                    time.sleep(0.2)

        except Exception as e:
            logger.critical(f"Fishing error: {e}")

        finally:
            mouse_up_right()
            logger.info("Right mouse button released")
            self.running = False
            logger.info("Fishing sequence stopped")

    def stop_fishing(self):
        self.running = False
        logger.info("Fishing manually stopped")

    def force_exit(self):
        logger.warning("Emergency exit triggered!")
        self.stop_fishing()
        os._exit(0)
