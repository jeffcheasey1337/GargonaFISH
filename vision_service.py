# vision_service.py
import cv2
import numpy as np
import mss
import logging

logger = logging.getLogger("VisionService")


def capture_screen(region=None):
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            if region:
                monitor = {
                    "top": region[1],
                    "left": region[0],
                    "width": region[2],
                    "height": region[3],
                    "mon": 1
                }

            img = np.array(sct.grab(monitor))
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    except Exception as e:
        logger.error(f"Screen capture error: {e}")
        return None


def find_splash(screen, color_range):
    if screen is None:
        return None

    try:
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        lower = np.array(color_range[0])
        upper = np.array(color_range[1])
        mask = cv2.inRange(hsv, lower, upper)

        # Улучшение обнаружения
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 50:
            return None

        x, y, w, h = cv2.boundingRect(largest)
        center = (x + w // 2, y + h // 2)
        logger.debug(f"Splash detected at {center}")
        return center
    except Exception as e:
        logger.error(f"Splash detection error: {e}")
        return None


def find_target_circle(screen, params):
    if screen is None:
        return None

    try:
        gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 2)

        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            **params
        )

        if circles is None:
            return None

        circles = np.uint16(np.around(circles))
        circle = circles[0][0]
        logger.debug(f"Target circle detected: {circle}")
        return (circle[0], circle[1], circle[2])
    except Exception as e:
        logger.error(f"Circle detection error: {e}")
        return None