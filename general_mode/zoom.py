# zoom.py - Pinch to Zoom In / Zoom Out (Ctrl + Scroll)

import autopy
import time
import math

# Settings
ZOOM_SENSITIVITY = 0.8     # lower = more sensitive
MIN_PINCH_DISTANCE = 50    # pixels to activate zoom
ZOOM_COOLDOWN = 0.15       # seconds between zoom steps

# State tracking
_last_zoom_time = 0
_prev_distance = None

def _can_zoom():
    global _last_zoom_time
    now = time.time()
    if now - _last_zoom_time >= ZOOM_COOLDOWN:
        _last_zoom_time = now
        return True
    return False

def zoom_in():
    if _can_zoom():
        autopy.key.toggle(autopy.key.Code.CONTROL, down=True)
        autopy.mouse.smooth_scroll(0, 2)   # scroll up = zoom in
        autopy.key.toggle(autopy.key.Code.CONTROL, down=False)

def zoom_out():
    if _can_zoom():
        autopy.key.toggle(autopy.key.Code.CONTROL, down=True)
        autopy.mouse.smooth_scroll(0, -2)  # scroll down = zoom out
        autopy.key.toggle(autopy.key.Code.CONTROL, down=False)

def check_zoom_gesture(thumb_tip, index_tip):
    """
    Call every frame when thumb + index are close.
    Compares current pinch distance with previous to detect expand/shrink.
    """
    global _prev_distance

    if not thumb_tip or not index_tip:
        _prev_distance = None
        return None

    # Calculate distance between thumb and index tip
    dx = thumb_tip[0] - index_tip[0]
    dy = thumb_tip[1] - index_tip[1]
    distance = math.hypot(dx, dy)

    if distance < MIN_PINCH_DISTANCE:
        if _prev_distance is None:
            _prev_distance = distance
            return None

        # Detect change in pinch distance
        diff = distance - _prev_distance

        if diff > ZOOM_SENSITIVITY:
            zoom_in()
            _prev_distance = distance
            return "in"
        elif diff < -ZOOM_SENSITIVITY:
            zoom_out()
            _prev_distance = distance
            return "out"

        _prev_distance = distance
    else:
        _prev_distance = None  # reset when fingers open

    return None