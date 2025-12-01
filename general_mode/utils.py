# utils.py - Shared utilities for the Haath K Ishaare project

import cv2
import time

# Global state reset (call when hand is lost)
def reset_all_states(modules=None):
    """
    Safely reset all module states when no hand is detected.
    Pass a dict like: {'cursor': cursor, 'click': click, ...}
    """
    if modules:
        for name, module in modules.items():
            if hasattr(module, 'reset'):
                module.reset()
            elif hasattr(module, 'release_all'):
                module.release_all()

# Distance between two landmarks
def get_distance(lm1, lm2):
    """Return Euclidean distance between two [x,y] points"""
    if lm1 is None or lm2 is None:
        return float('inf')
    return ((lm1[0] - lm2[0])**2 + (lm1[1] - lm2[1])**2)**0.5

# Cooldown decorator (optional advanced use)
def cooldown(seconds):
    last_called = 0
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal last_called
            now = time.time()
            if now - last_called >= seconds:
                result = func(*args, **kwargs)
                last_called = now
                return result
            return None
        return wrapper
    return decorator

# Draw status text on frame
def draw_status(img, text, position=(10, 50), color=(0, 255, 255), size=1.2, thickness=3):
    """Simple overlay text with background"""
    cv2.putText(img, text, position, cv2.FONT_HERSHEY_DUPLEX, 
                size, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(img, text, position, cv2.FONT_HERSHEY_DUPLEX, 
                size, color, thickness, cv2.LINE_AA)

# Draw active zone rectangle
def draw_active_zone(img, frame_reduction=100, color=(255, 0, 255), thickness=2):
    h, w = img.shape[:2]
    cv2.rectangle(img, 
                  (frame_reduction, frame_reduction),
                  (w - frame_reduction, h - frame_reduction),
                  color, thickness)

# FPS counter
class FPSCounter:
    def __init__(self):
        self.prev_time = time.time()
        self.fps = 0

    def update(self):
        current_time = time.time()
        self.fps = 1 / (current_time - self.prev_time) if current_time != self.prev_time else 0
        self.prev_time = current_time
        return int(self.fps)

    def draw(self, img, position=(20, 50)):
        draw_status(img, f'FPS: {self.fps:.1f}', position, (0, 255, 0), 1.2, 3)