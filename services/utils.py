import keyboard

_stop_flag = False

def set_stop_flag(value: bool):
    global _stop_flag
    _stop_flag = value

def get_stop_flag() -> bool:
    global _stop_flag
    return _stop_flag
def listen_for_stop_key(stop_key='k'):
    # Эта функция запускается в отдельном потоке или в main.py для отслеживания нажатия "k" для остановки
    keyboard.wait(stop_key)
    set_stop_flag(True)
