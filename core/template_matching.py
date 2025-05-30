import cv2
import numpy as np
import os
import logging

def load_template(template_path):
    if not os.path.exists(template_path):
        logging.warning(f"Шаблон не найден: {template_path}")
        return None
    template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
    if template is None:
        logging.error(f"Не удалось загрузить шаблон: {template_path}")
    return template

def find_template_with_mask(image, template_path, threshold=0.7):
    template = load_template(template_path)
    if template is None:
        return None, 0.0

    if template.shape[2] == 4:
        template_rgb = template[:, :, :3]
        alpha = template[:, :, 3]
        mask = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)[1]
    else:
        template_rgb = template
        mask = None

    method = cv2.TM_CCORR_NORMED
    if mask is not None:
        res = cv2.matchTemplate(image, template_rgb, method, mask=mask)
    else:
        res = cv2.matchTemplate(image, template_rgb, method)

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val < threshold:
        return None, max_val
    return max_loc, max_val

def find_all_templates(image, template_path, threshold=0.8):
    template = load_template(template_path)
    if template is None:
        return []

    if template.shape[2] == 4:
        template_rgb = template[:, :, :3]
    else:
        template_rgb = template

    if image.shape[2] != template_rgb.shape[2]:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    res = cv2.matchTemplate(image, template_rgb, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)

    results = []
    for pt in zip(*loc[::-1]):
        results.append((pt, res[pt[1], pt[0]]))

    return results

def get_template_center(top_left, template_path):
    template = load_template(template_path)
    if template is None:
        return None
    h, w = template.shape[:2]
    return (top_left[0] + w // 2, top_left[1] + h // 2)

def distance_points(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
