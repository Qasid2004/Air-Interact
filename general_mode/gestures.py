# gestures.py - ULTIMATE FLAWLESS VERSION (17 Nov 2025 – 10:24 PM PKT)
# Fixed: Double-click opens only ONCE + Perfect Drag + Zoom + Scroll + Volume

import cursor
import click
import pyautogui
import volume
import math
import time

class GestureManager:
    def __init__(self, cam_width, cam_height, frame_reduction=100, click_cooldown=0.5):
        self.cam_width = cam_width
        self.cam_height = cam_height
        self.frame_reduction = frame_reduction
        self.click_cooldown = click_cooldown

        # Volume
        self.prev_angle = 0.0
        self.last_set_vol = -1

        # Infinite Scroll
        self.last_index_y = None
        self.scroll_velocity = 0.0
        self.persistent_scroll_vel = 0.0
        self.scroll_sensitivity = 6.5
        self.scroll_smoothing = 0.34

        # Pinch Zoom
        self.last_pinch_dist = None
        self.zoom_velocity = 0.0
        self.persistent_zoom_vel = 0.0
        self.zoom_sensitivity = 0.032
        self.zoom_smoothing = 0.38

        # Drag state
        self.is_dragging = False

        # Double-click cooldown (prevents multiple opens)
        self.last_double_click_time = 0
        self.double_click_cooldown = 0.6  # 600 ms

        self.last_time = time.time()

    def process_gesture(self, lmList_left, lmList_right, fingers_left, fingers_right):
        now = time.time()
        dt = max(now - self.last_time, 0.001)
        self.last_time = now

        status = "SHOW HAND"
        holding_ctrl = False

        # === 1. FIST-TRIGGERED DRAG (Right index + Left fist) ===
        if (fingers_right and fingers_right == [0, 1, 0, 0, 0] and lmList_right):
            if fingers_left and sum(fingers_left) == 0:  # Left fist
                if not self.is_dragging:
                    pyautogui.mouseDown()
                    self.is_dragging = True
                cursor.move_cursor(lmList_right[8][1], lmList_right[8][2], self.cam_width, self.cam_height)
                status = "DRAG"
                return status, False
            else:
                if self.is_dragging:
                    pyautogui.mouseUp()
                    self.is_dragging = False
                cursor.move_cursor(lmList_right[8][1], lmList_right[8][2], self.cam_width, self.cam_height)
                status = "CURSOR"
                return status, False

        # === 2. PINCH ZOOM (Both hands L shape) ===
        if (fingers_left and fingers_left == [1, 1, 0, 0, 0] and
            fingers_right and fingers_right == [1, 1, 0, 0, 0] and
            lmList_left and lmList_right):

            l_ix, l_iy = lmList_left[8][1], lmList_left[8][2]
            r_ix, r_iy = lmList_right[8][1], lmList_right[8][2]
            dist = math.hypot(l_ix - r_ix, l_iy - r_iy)

            if self.last_pinch_dist is None:
                self.last_pinch_dist = dist
                self.zoom_velocity = self.persistent_zoom_vel
            else:
                delta = dist - self.last_pinch_dist
                target_vel = -delta * self.zoom_sensitivity / dt
                self.zoom_velocity += (target_vel - self.zoom_velocity) * self.zoom_smoothing
                self.persistent_zoom_vel = self.zoom_velocity
                amount = int(self.zoom_velocity * dt * 140)
                if abs(amount) >= 1:
                    pyautogui.keyDown('ctrl')
                    pyautogui.scroll(amount)
                    holding_ctrl = True
                self.last_pinch_dist = dist

            status = "PINCH ZOOM"
            return status, holding_ctrl

        # === 3. INFINITE SCROLL (Left palm + Right palm/fist) ===
        elif (fingers_left and all(fingers_left) and lmList_right):
            if fingers_right and all(fingers_right) and len(lmList_right) > 8:
                index_y = lmList_right[8][2]
                if self.last_index_y is None:
                    self.last_index_y = index_y
                    self.scroll_velocity = self.persistent_scroll_vel
                else:
                    dy = index_y - self.last_index_y
                    target = dy * self.scroll_sensitivity / dt
                    self.scroll_velocity += (target - self.scroll_velocity) * self.scroll_smoothing
                    self.persistent_scroll_vel = self.scroll_velocity
                    amt = int(self.scroll_velocity * dt)
                    if abs(amt) >= 1:
                        pyautogui.scroll(amt)
                    self.last_index_y = index_y
                status = "SCROLL"
                return status, False

            elif fingers_right and sum(fingers_right) <= 1:
                self.persistent_scroll_vel = self.scroll_velocity
                self.last_index_y = None
                self.scroll_velocity = 0.0
                status = "FIST → REPOSITION"
                return status, False

        # === AUTO-RELEASE DRAG if gesture changes ===
        if self.is_dragging:
            pyautogui.mouseUp()
            self.is_dragging = False

        # Reset zoom when not pinching
        self.last_pinch_dist = None
        self.zoom_velocity = 0.0
        self.persistent_zoom_vel = 0.0

        # === VOLUME & SINGLE-HAND GESTURES ===
        if fingers_right and all(fingers_right) and lmList_right and (not fingers_left or not all(fingers_left)):
            wx, wy = lmList_right[0][1], lmList_right[0][2]
            mx, my = lmList_right[9][1], lmList_right[9][2]
            angle = math.atan2(mx - wx, -(my - wy)) * 57.2958
            smoothed = self.prev_angle + (angle - self.prev_angle) / 5.0
            self.prev_angle = smoothed
            vol = int(((max(-90, min(90, -smoothed * 3.3)) + 90) / 180) * 20) * 5
            if abs(vol - self.last_set_vol) >= volume.VOLUME_STEP:
                volume.set_volume(vol)
                self.last_set_vol = vol
            status = f"VOLUME {self.last_set_vol}%"

        elif fingers_right and lmList_right:
            t, i, m, r, p = fingers_right

            # DOUBLE-CLICK — NOW ONLY ONCE (600 ms cooldown)
            if t and i and m and not r and not p:
                if now - self.last_double_click_time > self.double_click_cooldown:
                    pyautogui.doubleClick()
                    self.last_double_click_time = now
                status = "DOUBLE CLICK"

            elif i and m and not t and not r and not p:
                click.right_click()
                status = "RIGHT CLICK"

            elif i and t and not m and not r and not p:
                click.left_click()
                status = "LEFT CLICK"

        return status, False