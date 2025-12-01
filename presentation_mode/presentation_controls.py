# presentation_controls.py - FINAL PERFECT VERSION

import pyautogui
import numpy as np

screen_width, screen_height = pyautogui.size()

FRAME_REDUCTION = 120
SMOOTHING = 6          # Feels buttery smooth
PADDING = 0.22         # Reach every corner easily

prev_x = screen_width // 2
prev_y = screen_height // 2


def move_cursor(index_tip_x, index_tip_y, frame_width=640, frame_height=480):
    global prev_x, prev_y

    x_min = FRAME_REDUCTION
    x_max = frame_width - FRAME_REDUCTION
    y_min = FRAME_REDUCTION
    y_max = frame_height - FRAME_REDUCTION

    if not (x_min <= index_tip_x <= x_max and y_min <= index_tip_y <= y_max):
        return False, None

    # NO X-FLIP HERE → natural left/right movement!
    target_x = np.interp(index_tip_x, (x_min, x_max),
                         (-screen_width * PADDING, screen_width * (1 + PADDING)))
    target_y = np.interp(index_tip_y, (y_min, y_max),
                         (-screen_height * PADDING, screen_height * (1 + PADDING)))

    target_x = np.clip(target_x, 0, screen_width - 1)
    target_y = np.clip(target_y, 0, screen_height - 1)

    curr_x = prev_x + (target_x - prev_x) / SMOOTHING
    curr_y = prev_y + (target_y - prev_y) / SMOOTHING

    pyautogui.moveTo(curr_x, curr_y, duration=0)

    prev_x, prev_y = curr_x, curr_y
    return True, (int(curr_x), int(curr_y))