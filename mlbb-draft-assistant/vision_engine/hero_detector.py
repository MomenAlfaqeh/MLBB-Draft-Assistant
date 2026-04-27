import cv2
import numpy as np
import base64
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from vision_engine.template_matcher import TemplateMatcher

class HeroDetector:
    def __init__(self, matcher: TemplateMatcher = None):
        if matcher is None:
            matcher = TemplateMatcher()
        self.matcher = matcher
    
    def decode_base64_image(self, b64_string: str) -> np.ndarray:
        """
        Decode base64 string to OpenCV image (numpy array)
        """
        # Remove data URL prefix if present (e.g., "data:image/png;base64,")
        if ',' in b64_string:
            b64_string = b64_string.split(',')[1]
        
        # Decode base64
        img_data = base64.b64decode(b64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    
    def process_screenshot(self, img_bytes: bytes) -> dict:
        """
        Process a screenshot (as bytes) and return detected heroes
        For now, we'll decode the image and use the template matcher to detect heroes in the draft region.
        Returns a dict with keys "ally" and "enemy", each being a list of hero names.
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"ally": [], "enemy": []}
        
        # Use the matcher to detect picks
        detections = self.matcher.detect_all_picks(img)
        
        # For now, we'll return empty lists because the template matching for multiple slots is not implemented
        # In a real implementation, we would divide the draft region into slots and run match_hero on each slot.
        return {"ally": [], "enemy": []}

# Example usage (for testing)
if __name__ == "__main__":
    detector = HeroDetector()
    print("HeroDetector initialized")