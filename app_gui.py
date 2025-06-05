import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import logging
from config_service import load_config, update_bind_key, update_pause_key, update_speed, set_fishing_active, update_exit_key
from fishing_service import FishingManager
from tkinter import simpledialog
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
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=5)

        self.start_btn = ttk.Button(
            control_frame,
            text="Start Fishing",
            command=self.start_fishing,
            width=15
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        # 🧹 Удалена кнопка остановки

        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=5)

        ttk.Label(settings_frame, text="Bind Key:").grid(row=0, column=0, sticky=tk.W)
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(settings_frame, textvariable=self.key_var, width=5)
        self.key_entry.grid(row=0, column=1, padx=5)

        self.save_btn = ttk.Button(settings_frame, text="Save Key", command=self.save_key, width=10)
        self.save_btn.grid(row=0, column=2, padx=5)

        ttk.Label(settings_frame, text="Pause Key:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.pause_var = tk.StringVar()
        self.pause_entry = ttk.Entry(settings_frame, textvariable=self.pause_var, width=5)
        self.pause_entry.grid(row=1, column=1, padx=5, pady=(10, 0))
        self.pause_btn = ttk.Button(settings_frame, text="Save Pause", command=self.save_pause_key, width=10)
        self.pause_btn.grid(row=1, column=2, padx=5, pady=(10, 0))

        ttk.Label(settings_frame, text="Exit Key:").grid(row=3, column=0, sticky=tk.W, pady=(10, 0))
        self.exit_var = tk.StringVar()
        self.exit_entry = ttk.Entry(settings_frame, textvariable=self.exit_var, width=5)
        self.exit_entry.grid(row=3, column=1, padx=5, pady=(10, 0))
        self.exit_btn = ttk.Button(settings_frame, text="Save Exit", command=self.save_exit_key, width=10)
        self.exit_btn.grid(row=3, column=2, padx=5, pady=(10, 0))

        ttk.Label(settings_frame, text="Speed:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.speed_var = tk.IntVar(value=5)
        self.speed_scale = ttk.Scale(settings_frame, from_=1, to=10, orient=tk.HORIZONTAL,
                                     variable=self.speed_var, command=lambda e: self.save_speed())
        self.speed_scale.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(10, 0))

        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_logging_gui(self):
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                self.setFormatter(logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"))
                self.setLevel(logging.INFO)

            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.configure(state='normal')
                    if int(self.text_widget.index('end-1c').split('.')[0]) > 1000:
                        self.text_widget.delete(1.0, 100.0)
                    self.text_widget.insert(tk.END, msg + "\n")
                    self.text_widget.see(tk.END)
                    self.text_widget.configure(state='disabled')
                self.text_widget.after(0, append)

        logging.getLogger().addHandler(TextHandler(self.log_text))

    def update_ui(self):
        config = load_config()
        self.key_var.set(config.get('bind_key', 'e'))
        self.pause_var.set(config.get('pause_key', 'p'))
        self.speed_var.set(config.get('speed', 5))
        self.exit_var.set(config.get('exit_key', 'q'))

        if self.fishing_manager.running:
            self.start_btn.config(state=tk.DISABLED)
            self.status_var.set("Status: Fishing in progress...")
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.status_var.set("Status: Ready")

    def start_fishing(self):
        # Запрос выбора режима движения
        choice = messagebox.askquestion(
            "Выбор движения",
            "Двигаться к ближайшему всплеску? (Если 'Нет', будет движение в направлении)"
        )
        if choice == 'yes':
            # Двигаться к всплеску
            self.fishing_manager.set_move_mode('splash')
        else:
            # Запрос направления
            direction = simpledialog.askstring(
                "Выбор направления",
                "Введите направление движения: 'left' или 'right'"
            )
            if direction and direction.lower() in ('left', 'right'):
                self.fishing_manager.set_move_mode(direction.lower())
            else:
                messagebox.showerror("Ошибка", "Неверное направление, запускаю по всплескам")
                self.fishing_manager.set_move_mode('splash')

        # Далее запускаем поток рыбалки
        def fishing_thread():
            try:
                set_fishing_active(True)
                self.update_ui()
                self.fishing_manager.start_fishing()
            finally:
                self.root.after(100, self.update_ui)

        if not self.fishing_manager.running:
            threading.Thread(target=fishing_thread, daemon=True).start()
            logger.info("Fishing thread started")
        else:
            logger.warning("Fishing already running")
            messagebox.showwarning("Warning", "Fishing is already running")
    def save_key(self):
        key = self.key_var.get().strip().lower()
        if key and len(key) == 1:
            update_bind_key(key)
            logger.info(f"Bind key updated: {key}")
        else:
            messagebox.showerror("Error", "Invalid bind key")

    def save_pause_key(self):
        key = self.pause_var.get().strip().lower()
        if key and len(key) == 1:
            update_pause_key(key)
            logger.info(f"Pause key updated: {key}")
        else:
            messagebox.showerror("Error", "Invalid pause key")

    def save_speed(self):
        update_speed(self.speed_var.get())
        logger.info(f"Speed updated: {self.speed_var.get()}")

    def save_exit_key(self):
        key = self.exit_var.get().strip().lower()
        if key and len(key) == 1:
            update_exit_key(key)
            logger.info(f"Exit key updated: {key}")
        else:
            messagebox.showerror("Error", "Invalid exit key")


if __name__ == "__main__":
    from logger import setup_logging
    setup_logging()
    root = tk.Tk()
    app = FishingApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.fishing_manager.stop_fishing(), root.destroy()))
    root.mainloop()