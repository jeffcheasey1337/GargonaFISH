# app_gui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import logging
from config_service import load_config, update_bind_key, set_fishing_active
from fishing_service import FishingManager

logger = logging.getLogger("GUI")


class FishingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GTA V Fishing Bot")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        self.fishing_manager = FishingManager()
        self.create_widgets()
        self.setup_logging_gui()
        self.update_ui()
        logger.info("GUI initialized")

    def create_widgets(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Панель управления
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=5)

        self.start_btn = ttk.Button(
            control_frame,
            text="Start Fishing",
            command=self.start_fishing,
            width=15
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            control_frame,
            text="Stop Fishing",
            command=self.stop_fishing,
            width=15,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Панель настроек
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=5)

        ttk.Label(settings_frame, text="Bind Key:").grid(row=0, column=0, sticky=tk.W)

        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(
            settings_frame,
            textvariable=self.key_var,
            width=5
        )
        self.key_entry.grid(row=0, column=1, padx=5)

        self.save_btn = ttk.Button(
            settings_frame,
            text="Save Key",
            command=self.save_key,
            width=10
        )
        self.save_btn.grid(row=0, column=2, padx=5)

        # Логи
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            state='disabled',
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Статус бар
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_logging_gui(self):
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                self.setFormatter(logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%H:%M:%S"  # Укороченный формат времени
                ))
                self.setLevel(logging.INFO)

            def emit(self, record):
                msg = self.format(record)

                def append():
                    self.text_widget.configure(state='normal')
                    # Ограничение размера логов
                    if int(self.text_widget.index('end-1c').split('.')[0]) > 1000:
                        self.text_widget.delete(1.0, 100.0)
                    self.text_widget.insert(tk.END, msg + "\n")
                    self.text_widget.see(tk.END)
                    self.text_widget.configure(state='disabled')

                self.text_widget.after(0, append)

        text_handler = TextHandler(self.log_text)
        logging.getLogger().addHandler(text_handler)

    def update_ui(self):
        config = load_config()
        self.key_var.set(config.get('bind_key', 'e'))

        if self.fishing_manager.running:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_var.set("Status: Fishing in progress...")
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_var.set("Status: Ready")

    def start_fishing(self):
        def fishing_thread():
            try:
                # Устанавливаем флаг активности
                set_fishing_active(True)
                self.update_ui()
                self.fishing_manager.start_fishing()
            finally:
                self.root.after(100, self.update_ui)

        # Проверяем, не запущен ли уже процесс
        if not self.fishing_manager.running:
            threading.Thread(target=fishing_thread, daemon=True).start()
            logger.info("Fishing thread started")
        else:
            logger.warning("Fishing already running, ignoring start request")
            messagebox.showwarning("Warning", "Fishing is already running")

    def stop_fishing(self):
        self.fishing_manager.stop_fishing()
        self.update_ui()
        logger.info("Fishing stop requested")

    def save_key(self):
        new_key = self.key_var.get().strip().lower()
        if not new_key:
            messagebox.showerror("Error", "Key cannot be empty")
            return

        if len(new_key) != 1:
            messagebox.showerror("Error", "Please enter a single character key")
            return

        # Проверка текущего ключа перед обновлением
        current_key = load_config().get('bind_key', 'e')
        if new_key == current_key:
            messagebox.showinfo("Info", f"Key is already '{new_key}'")
            return

        if update_bind_key(new_key):
            messagebox.showinfo("Success", f"Key updated to '{new_key}'")
            logger.info(f"Key binding updated to {new_key}")
        else:
            messagebox.showerror("Error", "Failed to update key")
            logger.error(f"Failed to update key to {new_key}")


if __name__ == "__main__":
    from logger import setup_logging

    setup_logging()

    root = tk.Tk()
    app = FishingApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.fishing_manager.stop_fishing(), root.destroy()))
    root.mainloop()