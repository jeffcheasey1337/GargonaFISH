import json
import os
import logging

logger = logging.getLogger("ConfigService")
CONFIG_FILE = "fishing_config.json"

DEFAULT_CONFIG = {
    "bind_key": "e",
    "pause_key": "p",  # Добавлено
    "fishing_active": False,
    "speed": 5,
    "exit_key": "q",  # Клавиша для экстренного выхода
    "splash_color_range": [[90, 150, 50], [120, 255, 255]],
    "circle_params": {"dp": 1, "minDist": 100, "param1": 50, "param2": 30, "minRadius": 10, "maxRadius": 100}
}


def load_config():
    try:
        if not os.path.exists(CONFIG_FILE):
            logger.info("Config file not found, creating default")
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            logger.info("Config loaded successfully")
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}, using default")
        return DEFAULT_CONFIG.copy()


def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info("Config saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False


def update_bind_key(new_key):
    config = load_config()
    config['bind_key'] = new_key
    return save_config(config)


def update_pause_key(new_key):
    config = load_config()
    config['pause_key'] = new_key
    return save_config(config)


def update_speed(new_speed):
    config = load_config()
    config['speed'] = new_speed
    return save_config(config)


def set_fishing_active(state):
    config = load_config()
    config['fishing_active'] = state
    return save_config(config)
def update_exit_key(new_key):
    config = load_config()
    config['exit_key'] = new_key
    return save_config(config)
