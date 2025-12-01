import pyautogui
import numpy as np

screen_size = pyautogui.size()
wScr, hScr = screen_size.width, screen_size.height

FRAME_REDUCTION = 120       # ← Matches your setting
SMOOTHING = 8
PADDING = 0.20              # ← 20% extra reach → perfect corners & bottom

prev_x, prev_y = 0, 0

def move_cursor(index_tip_x, index_tip_y, frame_width=640, frame_height=480):
    global prev_x, prev_y

    x_min = FRAME_REDUCTION
    x_max = frame_width - FRAME_REDUCTION
    y_min = FRAME_REDUCTION
    y_max = frame_height - FRAME_REDUCTION

    if not (x_min < index_tip_x < x_max and y_min < index_tip_y < y_max):
        return False, None

    # Fix right-hand inversion
    index_tip_x = frame_width - index_tip_x

    # Map with padding + clamp safely
    x_screen = np.interp(index_tip_x, (x_min, x_max), (-wScr*PADDING, wScr*(1+PADDING)))
    y_screen = np.interp(index_tip_y, (y_min, y_max), (-hScr*PADDING, hScr*(1+PADDING)))
    x_screen = np.clip(x_screen, 1, wScr-1)
    y_screen = np.clip(y_screen, 1, hScr-1)

    # Smoothing
    curr_x = prev_x + (x_screen - prev_x) / SMOOTHING
    curr_y = prev_y + (y_screen - prev_y) / SMOOTHING

    pyautogui.moveTo(curr_x, curr_y)
    prev_x, prev_y = curr_x, curr_y
    return True, (curr_x, curr_y)