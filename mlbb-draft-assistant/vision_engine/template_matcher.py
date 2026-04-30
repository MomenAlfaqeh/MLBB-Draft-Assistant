import cv2
import numpy as np
import os
from typing import Dict, Tuple, Optional
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import TEMPLATE_MATCH_THRESHOLD, HERO_ICONS_PATH

ICON_MATCH_SIZE = (80, 80)


class TemplateMatcher:
    def __init__(self, icons_dir: str = None, threshold: float = None):
        if icons_dir is None:
            icons_dir = HERO_ICONS_PATH
        if threshold is None:
            threshold = TEMPLATE_MATCH_THRESHOLD

        self.icons_dir = icons_dir
        self.threshold = threshold
        self.templates: Dict[str, np.ndarray] = {}
        self.template_names: list = []
        self.template_array: Optional[np.ndarray] = None
        self.load_templates()

    def load_templates(self):
        self.templates = {}
        gray_templates = []
        self.template_names = []

        if not os.path.exists(self.icons_dir):
            os.makedirs(self.icons_dir)
            return

        for filename in sorted(os.listdir(self.icons_dir)):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                hero_name = os.path.splitext(filename)[0]
                img_path = os.path.join(self.icons_dir, filename)

                template = cv2.imread(img_path, cv2.IMREAD_COLOR)
                if template is not None:
                    resized = cv2.resize(template, ICON_MATCH_SIZE)
                    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                    normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

                    self.templates[hero_name] = normalized
                    gray_templates.append(normalized)
                    self.template_names.append(hero_name)

        if gray_templates:
            self.template_array = np.array(gray_templates)

        print(f"Loaded {len(self.templates)} hero templates from {self.icons_dir}")

    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        resized = cv2.resize(gray, ICON_MATCH_SIZE)
        normalized = cv2.normalize(resized, None, 0, 255, cv2.NORM_MINMAX)
        return normalized

    def match_region(self, region_img: np.ndarray) -> Tuple[Optional[str], float]:
        if self.template_array is None or len(self.template_names) == 0:
            return None, 0.0

        processed = self.preprocess_image(region_img)

        best_idx = -1
        best_confidence = 0.0

        for i, template in enumerate(self.template_array):
            result = cv2.matchTemplate(processed, template, cv2.TM_CCOEFF_NORMED)
            max_val = result.max()

            if max_val > best_confidence:
                best_confidence = max_val
                best_idx = i

        if best_confidence >= self.threshold and best_idx >= 0:
            return self.template_names[best_idx], round(float(best_confidence), 4)

        return None, round(float(best_confidence), 4)

    def detect_all_picks(self, full_screenshot: np.ndarray) -> Dict[str, list]:
        height = full_screenshot.shape[0]
        draft_region = full_screenshot[0:int(height * 0.25), :]
        return {"ally": [], "enemy": []}
