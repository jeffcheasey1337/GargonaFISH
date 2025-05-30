import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import logging
import queue
import time

from core.fishing import start_fishing
from services.utils import set_stop_flag
from services.config_reader import save_binded_key, read_binded_key

AVAILABLE_KEYS = [
    'mouse1', 'mouse2', 'space', 'k', 'l', 'left', 'right'
]

class FishingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GargonaFish - АвтоРыбалка")
        self.geometry("600x450")

        self.log_queue = queue.Queue()

        # Метка и выпадающий список для выбора кнопки
        ttk.Label(self, text="Выберите кнопку для рыбалки:").pack(pady=(10, 0))
        self.key_var = tk.StringVar()
        self.key_combobox = ttk.Combobox(self, values=AVAILABLE_KEYS, textvariable=self.key_var, state="readonly")
        self.key_combobox.pack(pady=(0, 5))

        # Загружаем сохранённую кнопку
        saved_key = read_binded_key()
        if saved_key and saved_key in AVAILABLE_KEYS:
            self.key_var.set(saved_key)
        else:
            self.key_var.set(AVAILABLE_KEYS[0])

        # Кнопка сохранить
        self.save_button = ttk.Button(self, text="Сохранить кнопку", command=self.save_keybind)
        self.save_button.pack(pady=5)

        # Кнопки Старт/Стоп
        self.start_button = ttk.Button(self, text="Старт", command=self.start_fishing_thread)
        self.start_button.pack(pady=10)

        self.stop_button = ttk.Button(self, text="Стоп", command=self.stop_fishing)
        self.stop_button.pack(pady=10)
        self.stop_button.config(state=tk.DISABLED)

        # Текстовое поле для логов
        self.log_text = scrolledtext.ScrolledText(self, height=15, state='disabled')
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)

        # Запускаем обработчик логов
        self.after(100, self.process_log_queue)

        # Настройка логгера
        self.setup_logger()

    def setup_logger(self):
        class QueueHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue

            def emit(self, record):
                log_entry = self.format(record)
                self.log_queue.put(log_entry)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', '%H:%M:%S')
        handler.setFormatter(formatter)
        logger.handlers = [handler]

    def process_log_queue(self):
        try:
            while True:
                record = self.log_queue.get_nowait()
                self.log_text.config(state='normal')
                self.log_text.insert('end', record + '\n')
                self.log_text.see('end')
                self.log_text.config(state='disabled')
        except queue.Empty:
            pass
        self.after(100, self.process_log_queue)

    def save_keybind(self):
        selected_key = self.key_var.get()
        save_binded_key(selected_key)
        logging.info(f"Клавиша '{selected_key}' успешно сохранена!")

    def start_fishing_thread(self):
        key = self.key_var.get()
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        logging.info(f"Запуск рыбалки через 5 секунд с клавишей: {key}...")
        threading.Thread(target=self.run_fishing, args=(key,), daemon=True).start()

    def run_fishing(self, key):
        time.sleep(5)
        start_fishing(key)
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def stop_fishing(self):
        set_stop_flag()
        logging.info("Остановка рыбалки по кнопке.")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = FishingApp()
    app.mainloop()
