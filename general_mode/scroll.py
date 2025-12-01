# scroll.py - Vertical & Horizontal Scroll + Presentation Mode

import autopy
import time

# Scroll settings
SCROLL_SPEED_VERT = 3      # lines per frame (higher = faster)
SCROLL_SPEED_HORZ = 2
SCROLL_DEADZONE = 15       # pixels - prevents jitter
HOLD_TIME_FOR_MODE = 1.2   # seconds palm open → enter scroll mode

# State tracking
_scroll_mode = False
_last_palm_time = 0
_last_y = 0
_last_x = 0

def enter_scroll_mode():
    """Called when palm is open for long enough"""
    global _scroll_mode, _last_palm_time
    _scroll_mode = True
    _last_palm_time = time.time()
    print("Scroll Mode Activated")

def exit_scroll_mode():
    """Leave scroll mode"""
    global _scroll_mode
    if _scroll_mode:
        print("Scroll Mode Deactivated")
    _scroll_mode = False

def is_in_scroll_mode():
    return _scroll_mode

def vertical_scroll(hand_center_y, current_y=None):
    """
    Scroll up/down based on hand movement.
    Positive = scroll down, Negative = scroll up (natural feel)
    """
    global _last_y

    if not _scroll_mode:
        return

    if _last_y == 0:
        _last_y = hand_center_y
        return

    dy = hand_center_y - _last_y

    if abs(dy) > SCROLL_DEADZONE:
        lines = int(dy / 10) * SCROLL_SPEED_VERT
        if lines != 0:
            autopy.mouse.smooth_scroll(0, -lines)  # negative = up
        _last_y = hand_center_y

def horizontal_scroll(hand_center_x):
    """
    Left/Right scroll (great for presentations, timelines, etc.)
    """
    global _last_x

    if not _scroll_mode:
        return

    if _last_x == 0:
        _last_x = hand_center_x
        return

    dx = hand_center_x - _last_x

    if abs(dx) > SCROLL_DEADZONE:
        clicks = int(dx / 12) * SCROLL_SPEED_HORZ
        if clicks != 0:
            autopy.mouse.smooth_scroll(-clicks, 0)  # negative = left
        _last_x = hand_center_x

def update_palm_timer(is_palm_open):
    """
    Call every frame: detects how long palm is open
    """
    global _last_palm_time

    if is_palm_open:
        if time.time() - _last_palm_time > HOLD_TIME_FOR_MODE and not _scroll_mode:
            enter_scroll_mode()
    else:
        _last_palm_time = time.time()
        if _scroll_mode:
            exit_scroll_mode()
        _last_y = 0
        _last_x = 0

def reset_scroll():
    """Call when hand is lost or on exit"""
    global _last_y, _last_x
    exit_scroll_mode()
    _last_y = 0
    _last_x = 0