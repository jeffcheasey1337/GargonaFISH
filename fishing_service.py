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
        self.move_mode = 'splash'
        self.circle_range = (0, 0)
        self.circle_speed = 100
        self.circle_start_position = (0, 0)
        # Изменяем на вертикальные позиции
        self.circle_y_positions = []  # ТЕПЕРЬ ОТСЛЕЖИВАЕМ ВЕРТИКАЛЬНЫЕ ПОЗИЦИИ
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

    def find_calibration_circle(self):
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower_color = np.array([79, 87, 52])
        upper_color = np.array([107, 118, 56])

        mask = cv2.inRange(hsv, lower_color, upper_color)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected_circles = []
        average_radius = 0

        for i, cnt in enumerate(contours):
            ((x, y), radius) = cv2.minEnclosingCircle(cnt)
            area = cv2.contourArea(cnt)
            circle_area = math.pi * (radius ** 2)

            if radius < 15 or radius > 100:
                continue
            if circle_area == 0:
                continue

            fill_ratio = area / circle_area
            if fill_ratio < 0.6:
                continue

            detected_circles.append((int(x), int(y)))
            average_radius += radius

        if detected_circles:
            average_radius /= len(detected_circles)
        return detected_circles, average_radius

    def perform_calibration(self, min_samples, max_duration, session_dir, prefix=""):
        """Выполняет калибровку до сбора min_samples или истечения max_duration"""
        calibration_data = []
        calibration_start = time.time()
        calibration_step = 0

        logger.info(f"Starting calibration cycle: {prefix} (min_samples={min_samples}, max_duration={max_duration})")
        mouse_down_right()
        time.sleep(0.2)

        while (time.time() - calibration_start < max_duration and
               len(calibration_data) < min_samples and
               self.running and not self.paused):

            circles, circle_size = self.find_calibration_circle()
            current_time = time.time() - calibration_start

            if circles:
                current_pos = pyautogui.position()
                closest_circle = min(
                    circles,
                    key=lambda p: math.sqrt((p[0] - current_pos[0]) ** 2 + (p[1] - current_pos[1]) ** 2)
                )

                calibration_data.append({
                    "time": current_time,
                    "position": closest_circle,
                    "size": circle_size
                })

                self.circle_y_positions.append(closest_circle[1])
                logger.debug(f"Calibration sample {len(calibration_data)} collected at {closest_circle}")

                debug_path = os.path.join(session_dir, f"{prefix}calib_step_{calibration_step}.png")
                self.make_debug_screenshot(debug_path, [], (0, 0), highlight_point=closest_circle)
                calibration_step += 1
            else:
                current_pos = pyautogui.position()
                self.circle_y_positions.append(current_pos[1])

            time.sleep(0.1)

        mouse_up_right()
        logger.info(f"Calibration cycle completed: {prefix}. Collected {len(calibration_data)} samples")
        return calibration_data

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
        threshold = 0.75
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

        # Фильтрация по диапазону круга наведения
        if hasattr(self, 'circle_range') and self.circle_range != (0, 0):
            min_y, max_y = self.circle_range
            filtered_points = [p for p in filtered_points if min_y <= p[1] <= max_y]
            logger.debug(f"Filtered {len(filtered_points)} splashes within circle range")

        logger.debug(f"Found {len(filtered_points)} splashes by template matching")
        return filtered_points, w, h

    def make_debug_screenshot(self, path, splashes, splash_size, highlight_point=None, circle_range=None,
                              route_positions=None):
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

        # ВИЗУАЛИЗАЦИЯ ВЕРТИКАЛЬНОГО МАРШРУТА
        if route_positions:
            overlay = img.copy()
            min_y = min(route_positions)
            max_y = max(route_positions)

            # Рисуем вертикальную полосу маршрута
            width = 20  # Ширина полосы
            center_x = img.shape[1] // 2  # Центр экрана по горизонтали
            left_x = center_x - width // 2
            right_x = center_x + width // 2

            # Закрашиваем область маршрута
            cv2.rectangle(overlay, (left_x, min_y), (right_x, max_y), (0, 255, 255), -1)

            # Добавляем границы маршрута
            cv2.rectangle(overlay, (left_x, min_y), (right_x, max_y), (0, 200, 255), 2)

            # Добавляем текст
            cv2.putText(overlay, f"Route: {min_y}-{max_y}",
                        (left_x, min_y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 200, 255), 2)

            # Применяем прозрачность
            alpha = 0.3
            img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

            # Отмечаем начальную и конечную точки
            cv2.circle(img, (center_x, min_y), 8, (0, 100, 255), -1)
            cv2.circle(img, (center_x, max_y), 8, (0, 100, 255), -1)

        # Визуализация вертикального диапазона круга (без изменений)
        if circle_range:
            min_y, max_y = circle_range
            # Преобразование в целые числа
            min_y = int(min_y)
            max_y = int(max_y)

            cv2.line(img, (0, min_y), (img.shape[1], min_y), (0, 255, 0), 2)
            cv2.line(img, (0, max_y), (img.shape[1], max_y), (0, 255, 0), 2)
            cv2.putText(img, f"Y-range: {min_y}-{max_y}",
                        (10, min_y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)

        cv2.imwrite(path, img)

    def save_route_visualization(self, session_dir):
        """Сохраняет скриншот с визуализацией всего маршрута круга (вертикального)"""
        if not self.circle_y_positions:
            return

        screenshot = pyautogui.screenshot()
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # Определяем диапазон вертикального движения
        min_y = min(self.circle_y_positions)
        max_y = max(self.circle_y_positions)
        avg_x = pyautogui.size().width // 2  # Центр экрана по горизонтали

        # Создаем прозрачный слой
        overlay = img.copy()

        # Рисуем вертикальную полосу маршрута
        width = 30
        left_x = avg_x - width // 2
        right_x = avg_x + width // 2

        # Закрашиваем область маршрута
        cv2.rectangle(overlay, (left_x, min_y), (right_x, max_y), (0, 165, 255), -1)

        # Добавляем границы
        cv2.rectangle(overlay, (left_x, min_y), (right_x, max_y), (0, 100, 255), 3)

        # Добавляем текст
        cv2.putText(overlay, f"Circle Route: {min_y}px to {max_y}px",
                    (left_x, min_y - 15), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 100, 255), 2)

        # Отмечаем ключевые точки
        cv2.circle(overlay, (avg_x, min_y), 12, (0, 0, 255), -1)
        cv2.circle(overlay, (avg_x, max_y), 12, (0, 0, 255), -1)
        cv2.putText(overlay, "Start", (left_x - 100, min_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(overlay, "End", (right_x + 10, max_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Применяем прозрачность
        alpha = 0.25
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

        # Сохраняем результат
        path = os.path.join(session_dir, "circle_route_visualization.png")
        cv2.imwrite(path, img)
        logger.info(f"Vertical circle route visualization saved: {path}")

    def start_fishing(self):
        if self.running:
            logger.warning("Fishing already running")
            return

        self.running = True
        self.paused = False
        self.circle_x_positions = []  # Сбрасываем историю позиций
        self.config = load_config()
        pause_key = self.config.get("pause_key", "p")
        exit_key = self.config.get("exit_key", "q")
        calibration_duration = self.config.get("calibration_duration", 10)

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

            # Основная калибровка: продолжать до сбора 10 образцов или 20 секунд
            calibration_data = []
            min_samples = 10
            max_duration = 20

            # Этап 1: Первичная калибровка
            calibration_data += self.perform_calibration(min_samples, max_duration, session_dir, "primary_")

            # Если не собрали достаточно образцов, попробуем еще раз
            if len(calibration_data) < min_samples:
                logger.warning(f"Primary calibration collected only {len(calibration_data)} samples, retrying...")
                calibration_data += self.perform_calibration(min_samples - len(calibration_data),
                                                             max_duration,
                                                             session_dir,
                                                             "retry_")

            # Этап 2: Дополнительная калибровка после сбора основных данных
            if calibration_data:
                logger.info("Performing additional calibration")
                additional_data = self.perform_calibration(5,  # Собрать еще 5 образцов
                                                           10,  # максимум 10 секунд
                                                           session_dir,
                                                           "additional_")
                calibration_data += additional_data
                logger.info(f"Additional calibration collected {len(additional_data)} samples")
            else:
                logger.error("No calibration data collected, skipping additional calibration")

            # Сохраняем визуализацию маршрута
            self.save_route_visualization(session_dir)
            logger.info(f"Total calibration samples: {len(calibration_data)}")

            if calibration_data:
                y_positions = [d['position'][1] for d in calibration_data]

                if len(y_positions) > 1:
                    y_diff = np.diff(y_positions)
                    avg_vertical_speed = np.mean(np.abs(y_diff)) / 0.1
                else:
                    avg_vertical_speed = 100

                min_y = int(min(y_positions)) - 50
                max_y = int(max(y_positions)) + 50

                self.circle_range = (min_y, max_y)
                self.circle_speed = avg_vertical_speed

                screen_width, screen_height = pyautogui.size()
                start_y = np.mean([d['position'][1] for d in calibration_data[:5]]) if len(calibration_data) >= 5 else (
                                                                                                                                   min_y + max_y) // 2
                self.circle_start_position = (screen_width // 2, int(start_y))

                logger.info(f"Vertical movement range: Y={min_y}-{max_y}")
                logger.info(f"Average vertical speed: {avg_vertical_speed:.1f} px/s")
                logger.info(f"Typical start position: {self.circle_start_position}")
            else:
                logger.warning("No calibration data collected - using defaults")
                screen_width, screen_height = pyautogui.size()
                min_y = int(screen_height * 0.3)
                max_y = int(screen_height * 0.7)
                self.circle_range = (min_y, max_y)
                self.circle_speed = 100
                self.circle_start_position = (screen_width // 2, screen_height // 2)

            # Сохраняем скриншот с диапазоном и маршрутом
            debug_path = os.path.join(session_dir, "step_0_after_calibration.png")
            self.make_debug_screenshot(
                debug_path,
                [],
                (0, 0),
                circle_range=self.circle_range,
                route_positions=self.circle_x_positions
            )

            # Основной цикл поиска и наведения
            speed = self.config.get('speed', 5)
            max_step = 20 * speed
            step_num = 1

            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue

                # Поиск всплесков БЕЗ удержания ПКМ
                splashes, w, h = self.find_splashes()

                if not splashes:
                    logger.info("No splashes found, waiting...")
                    time.sleep(0.5)
                    continue

                # Выбор цели
                current_pos = pyautogui.position()
                target = min(
                    splashes,
                    key=lambda p: (p[0] - current_pos[0]) ** 2 + (p[1] - current_pos[1]) ** 2
                )
                logger.info(f"New target splash at {target}")

                # Наведение на цель
                mouse_down_right()
                time.sleep(0.2)

                # Плавное движение к цели
                reached = move_towards(target, max_step)

                # Отладочный скриншот с маршрутом и диапазоном
                debug_path = os.path.join(session_dir, f"step_{step_num}_move.png")
                self.make_debug_screenshot(
                    debug_path,
                    splashes,
                    (w, h),
                    highlight_point=target,
                    circle_range=self.circle_range,
                    route_positions=self.circle_x_positions
                )
                step_num += 1

                # Отпускание после достижения цели
                mouse_up_right()
                logger.info("Target reached, released RMB")

                # Пауза между действиями
                time.sleep(1)

        except Exception as e:
            logger.critical(f"Fishing error: {e}")
            import traceback
            logger.error(traceback.format_exc())

        finally:
            if pyautogui.mouseUp is not None:
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