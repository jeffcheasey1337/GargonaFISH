import cv2
import numpy as np
import mss
import json
from datetime import datetime

hsv_frame = None
saved_colors = []

def list_monitors():
    with mss.mss() as sct:
        monitors = sct.monitors
        print("Доступные экраны:")
        for i, m in enumerate(monitors):
            if i == 0:
                print(f"{i}: Все мониторы (виртуальный экран)")
            else:
                print(f"{i}: Монитор {i} - {m}")
        return monitors

def select_monitor(monitors):
    while True:
        try:
            index = int(input("Выберите номер монитора: "))
            if 0 <= index < len(monitors):
                return monitors[index]
            else:
                print("Некорректный номер. Попробуйте снова.")
        except ValueError:
            print("Введите число.")

def mouse_callback(event, x, y, flags, param):
    global hsv_frame, saved_colors
    if hsv_frame is None:
        return

    hsv_value = hsv_frame[y, x]
    h, s, v = hsv_value
    lower = np.clip(hsv_value - np.array([10, 50, 50]), 0, 255)
    upper = np.clip(hsv_value + np.array([10, 50, 50]), 0, 255)

    if event == cv2.EVENT_MOUSEMOVE:
        print(f"Навели HSV: {hsv_value} | Нижняя: {lower} | Верхняя: {upper}", end="\r")

    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"\n💾 Сохраняем HSV: {hsv_value} | Нижняя: {lower} | Верхняя: {upper}")
        saved_colors.append({
            "timestamp": datetime.now().isoformat(),
            "hsv": hsv_value.tolist(),
            "lower": lower.tolist(),
            "upper": upper.tolist()
        })
        save_to_file(saved_colors)

def save_to_file(data):
    with open("saved_hsv_ranges.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def start_hsv_picker(monitor):
    global hsv_frame
    with mss.mss() as sct:
        cv2.namedWindow("Экран")
        cv2.setMouseCallback("Экран", mouse_callback)

        while True:
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            cv2.imshow("Экран", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()

if __name__ == "__main__":
    monitors = list_monitors()
    selected_monitor = select_monitor(monitors)
    print(f"Захват экрана: {selected_monitor}")
    start_hsv_picker(selected_monitor)
