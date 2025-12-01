# click.py - Left Click, Right Click & Click-and-Drag (Hold)

import pyautogui
import time

# State tracking
_left_down = False
_right_down = False
_last_left_click_time = 0
_last_right_click_time = 0
CLICK_COOLDOWN = 0.3  # seconds - prevents double-trigger

def left_click():
    """Single left click with cooldown"""
    global _last_left_click_time
    now = time.time()
    if now - _last_left_click_time >= CLICK_COOLDOWN:
        pyautogui.click(button='left')
        _last_left_click_time = now

def right_click():
    """Single right click with cooldown"""
    global _last_right_click_time
    now = time.time()
    if now - _last_right_click_time >= CLICK_COOLDOWN:
        pyautogui.click(button='right')
        _last_right_click_time = now

def start_left_drag():
    """Press and hold left button (for dragging/text selection)"""
    global _left_down
    if not _left_down:
        pyautogui.mouseDown(button='left')
        _left_down = True

def stop_left_drag():
    """Release left button"""
    global _left_down
    if _left_down:
        pyautogui.mouseUp(button='left')
        _left_down = False  # Fixed: was True before

def start_right_drag():
    global _right_down
    if not _right_down:
        pyautogui.mouseDown(button='right')
        _right_down = True

def stop_right_drag():
    global _right_down
    if _right_down:
        pyautogui.mouseUp(button='right')
        _right_down = False

def release_all():
    """Emergency release - call on exit or gesture reset"""
    stop_left_drag()
    stop_right_drag()