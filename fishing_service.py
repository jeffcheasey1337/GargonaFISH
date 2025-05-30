import time
import logging
import threading
import tkinter as tk
from input_service import press_key, move_mouse_relative, mouse_down_right, mouse_up_right
from config_service import load_config

logger = logging.getLogger("FishingService")


class FishingManager:
    def __init__(self):
        self.running = False
        self.config = load_config()
        self.direction = None  # "left" или "right"
        logger.info("Fishing manager initialized")

    def select_direction(self):
        direction_selected = threading.Event()

        def choose_left():
            self.direction = "left"
            direction_selected.set()
            window.destroy()

        def choose_right():
            self.direction = "right"
            direction_selected.set()
            window.destroy()

        window = tk.Tk()
        window.title("Выбор направления")
        window.geometry("200x100")
        window.resizable(False, False)

        tk.Label(window, text="Выберите направление:").pack(pady=5)
        tk.Button(window, text="Влево", width=10, command=choose_left).pack(side="left", padx=20, pady=10)
        tk.Button(window, text="Вправо", width=10, command=choose_right).pack(side="right", padx=20, pady=10)

        window.mainloop()
        direction_selected.wait()

    def start_fishing(self):
        if self.running:
            logger.warning("Fishing already running")
            return

        self.running = True
        logger.info("Starting fishing sequence")

        try:
            self.select_direction()

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

            # Увеличиваем dx в 5 раз
            dx = (-20 if self.direction == "left" else 20) * 5  # = -100 или 100

            while self.running:
                move_mouse_relative(dx, 0)
                time.sleep(0.05)

        except Exception as e:
            logger.critical(f"Fishing error: {e}")

        finally:
            mouse_up_right()
            logger.info("Right mouse button released")
            self.running = False
            logger.info("Fishing sequence stopped")

    def stop_fishing(self):
        if self.running:
            logger.info("Stopping fishing sequence")
            self.running = False
        else:
            logger.warning("Fishing not running, nothing to stop")
