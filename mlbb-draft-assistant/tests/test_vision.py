import pytest
import numpy as np
import base64
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from vision_engine.template_matcher import TemplateMatcher
from vision_engine.hero_detector import HeroDetector

def test_preprocess_image_returns_correct_shape():
    """Test that preprocess_image returns correct shape"""
    matcher = TemplateMatcher()
    
    # Create a 200x200x3 color image (BGR)
    test_img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    
    # Preprocess the image
    processed = matcher.preprocess_image(test_img)
    
    # Assert output shape is (64, 64) - grayscale
    assert processed.shape == (64, 64)
    assert len(processed.shape) == 2  # Should be grayscale (2D)

def test_decode_base64_image():
    """Test that decode_base64_image works correctly"""
    detector = HeroDetector()
    
    # Create a small test image (10x10 pixels, 3 channels)
    test_img = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
    
    # Encode to base64
    _, buffer = cv2.imencode('.png', test_img)
    b64_string = base64.b64encode(buffer).decode('utf-8')
    
    # Decode back to image
    decoded_img = detector.decode_base64_image(b64_string)
    
    # Assert we got a valid numpy array
    assert isinstance(decoded_img, np.ndarray)
    assert decoded_img.shape == (10, 10, 3)  # Should be same size as original

# Need to import cv2 for the test
import cv2

if __name__ == "__main__":
    pytest.main([__file__])