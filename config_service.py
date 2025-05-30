# config_service.py
import json
import os
import logging

logger = logging.getLogger("ConfigService")
CONFIG_FILE = "fishing_config.json"

DEFAULT_CONFIG = {
    "bind_key": "e",
    "fishing_active": False,
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
    if new_key == config.get('bind_key'):
        logger.warning("Same key provided, no changes made")
        return True  # Возвращаем True, так как это не ошибка

    config['bind_key'] = new_key
    if save_config(config):
        logger.info(f"Key updated to '{new_key}'")
        return True
    return False


def set_fishing_active(state):
    config = load_config()
    if config.get('fishing_active') == state:
        return True

    config['fishing_active'] = state
    return save_config(config)