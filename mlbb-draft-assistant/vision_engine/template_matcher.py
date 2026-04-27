import cv2
import numpy as np
import os
from typing import Dict, Tuple, Optional, List
import sys

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import TEMPLATE_MATCH_THRESHOLD, HERO_ICONS_PATH

class TemplateMatcher:
    def __init__(self, icons_dir: str = None, threshold: float = None):
        if icons_dir is None:
            icons_dir = HERO_ICONS_PATH
        if threshold is None:
            threshold = TEMPLATE_MATCH_THRESHOLD
        
        self.icons_dir = icons_dir
        self.threshold = threshold
        self.templates: Dict[str, np.ndarray] = {}
        self.load_templates()
    
    def load_templates(self) -> Dict[str, np.ndarray]:
        """Load all hero icon images from folder"""
        self.templates = {}
        
        # Create directory if it doesn't exist
        if not os.path.exists(self.icons_dir):
            os.makedirs(self.icons_dir)
            print(f"Created icons directory: {self.icons_dir}")
            return self.templates
        
        # Load all .png and .jpg files
        for filename in os.listdir(self.icons_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Remove extension to get hero name
                hero_name = os.path.splitext(filename)[0]
                img_path = os.path.join(self.icons_dir, filename)
                
                # Load image
                template = cv2.imread(img_path, cv2.IMREAD_COLOR)
                if template is not None:
                    self.templates[hero_name] = template
                else:
                    print(f"Warning: Could not load image {img_path}")
        
        print(f"Loaded {len(self.templates)} hero templates from {self.icons_dir}")
        return self.templates
    
    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """Convert to grayscale and resize to standard size"""
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # Resize to 64x64
        resized = cv2.resize(gray, (64, 64))
        return resized
    
    def match_hero(self, screenshot_region: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Match a screenshot region against loaded templates
        Returns (hero_name, confidence) or (None, 0.0)
        """
        if not self.templates:
            return None, 0.0
        
        # Preprocess the screenshot region
        processed_region = self.preprocess_image(screenshot_region)
        
        best_match_name = None
        best_confidence = 0.0
        
        # Match against each template
        for hero_name, template in self.templates.items():
            # Preprocess template
            processed_template = self.preprocess_image(template)
            
            # Template matching
            result = cv2.matchTemplate(processed_region, processed_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            if max_val > best_confidence and max_val >= self.threshold:
                best_confidence = max_val
                best_match_name = hero_name
        
        return best_match_name, best_confidence
    
    def detect_all_picks(self, full_screenshot: np.ndarray) -> Dict[str, List[str]]:
        """
        Detect hero picks from full screenshot
        Returns dict with "ally" and "enemy" lists
        """
        # For simplicity, we'll assume the draft region is in the top 25% of the screenshot
        height = full_screenshot.shape[0]
        draft_region = full_screenshot[0:int(height * 0.25), :]
        
        # In a real implementation, we would divide this region into slots
        # and match each slot against templates
        # For now, we'll return empty lists as this is a scaffold
        return {"ally": [], "enemy": []}

# Example usage (for testing)
if __name__ == "__main__":
    matcher = TemplateMatcher()
    print(f"Matcher loaded with {len(matcher.templates)} templates")