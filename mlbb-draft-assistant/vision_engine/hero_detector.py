import cv2
import numpy as np
import base64
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from vision_engine.template_matcher import TemplateMatcher
from vision_engine.screen_regions import DRAFT_REGIONS, get_pixel_regions


class HeroDetector:
    def __init__(self, matcher: TemplateMatcher = None):
        if matcher is None:
            matcher = TemplateMatcher()
        self.matcher = matcher

    def decode_base64_image(self, b64_string: str) -> np.ndarray:
        if ',' in b64_string:
            b64_string = b64_string.split(',')[1]

        img_data = base64.b64decode(b64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    def detect_draft(self, screenshot_base64: str) -> dict:
        img = self.decode_base64_image(screenshot_base64)
        if img is None:
            return self._empty_result()

        height, width = img.shape[:2]
        pixel_regions = get_pixel_regions(width, height)

        result = {
            "ally_bans": [],
            "enemy_bans": [],
            "ally_picks": [],
            "enemy_picks": [],
            "confidence_scores": {}
        }

        for category in ["ally_bans", "enemy_bans", "ally_picks", "enemy_picks"]:
            slots = pixel_regions.get(category, [])
            for slot_idx, (x1, y1, x2, y2) in enumerate(slots):
                region = img[y1:y2, x1:x2]
                hero_name, confidence = self.matcher.match_region(region)

                result[category].append(hero_name)

                key = f"{category}_{slot_idx}"
                result["confidence_scores"][key] = {
                    "hero": hero_name,
                    "confidence": confidence
                }

        return result

    def process_screenshot(self, img_bytes: bytes) -> dict:
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return {"ally": [], "enemy": []}

        detections = self.matcher.detect_all_picks(img)
        return {"ally": [], "enemy": []}

    def _empty_result(self) -> dict:
        return {
            "ally_bans": [None] * 4,
            "enemy_bans": [None] * 4,
            "ally_picks": [None] * 5,
            "enemy_picks": [None] * 5,
            "confidence_scores": {}
        }
