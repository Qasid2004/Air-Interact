# presentation_gestures.py - FINAL WORKING VERSION (NO PLACEHOLDERS)

import cv2
import pyautogui
import time
import mediapipe as mp
import presentation_controls as cursor

class handDetector:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.8, trackCon=0.8):
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=mode,
            max_num_hands=maxHands,
            model_complexity=1,
            min_detection_confidence=detectionCon,
            min_tracking_confidence=trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=False):
        lmList = []
        if self.results.multi_hand_landmarks and len(self.results.multi_hand_landmarks) > handNo:
            myHand = self.results.multi_hand_landmarks[handNo]
            h, w, _ = img.shape
            for id, lm in enumerate(myHand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 7, (255, 0, 255), -1)
        return lmList

    def getHandedness(self, handNo=0):
        if self.results.multi_handedness and len(self.results.multi_handedness) > handNo:
            return self.results.multi_handedness[handNo].classification[0].label
        return "Unknown"

    def fingersUp(self, lmList):
        if not lmList:
            return [0, 0, 0, 0, 0]

        fingers = []

        # Thumb
        if lmList[4][1] < lmList[3][1]:        # tip left of IP joint → thumb up
            fingers.append(1)
        else:
            fingers.append(0)

        # Index to Pinky
        for i in range(1, 5):
            tip_y = lmList[self.tipIds[i]][2]
            pip_y = lmList[self.tipIds[i] - 2][2]
            fingers.append(1 if tip_y < pip_y - 15 else 0)

        return fingers


class GestureManager:
    def __init__(self, cam_width=640, cam_height=480, frame_reduction=120):
        self.cam_width = cam_width
        self.cam_height = cam_height
        self.frame_reduction = frame_reduction
        self.is_drawing = False

        # Anti-spam cooldown
        self.cooldown = 1.4
        self.last_next = 0
        self.last_prev = 0
        self.last_undo = 0

        self.auto_pen = True   # automatically press Ctrl+P when you start drawing

    def process_gesture(self, lmList_left, lmList_right, fingers_left, fingers_right):
        now = time.time()

        # Use ANY hand (left or right)
        hand_lm = lmList_right or lmList_left
        hand_fingers = fingers_right or fingers_left

        if not hand_lm:
            if self.is_drawing:
                pyautogui.mouseUp()
                self.is_drawing = False
            return "NO HAND", False

        idx_x, idx_y = hand_lm[8][1], hand_lm[8][2]

        # PREV SLIDE — Thumb only
        if hand_fingers == [1, 0, 0, 0, 0]:
            if now - self.last_next > self.cooldown:
                pyautogui.press('left')
                self.last_next = now
            if self.is_drawing:
                pyautogui.mouseUp()
                self.is_drawing = False
            return "PREV SLIDE", False

        # NEXT SLIDE — Fist
        elif hand_fingers == [0, 0, 0, 0, 0]:
            if now - self.last_prev > self.cooldown:
                pyautogui.press('right')
                self.last_prev = now
            if self.is_drawing:
                pyautogui.mouseUp()
                self.is_drawing = False
            return "NEXT SLIDE", False

        # DOODLE — Index + Middle
        # elif hand_fingers == [0, 1, 1, 0, 0]:
        #     if not self.is_drawing and self.auto_pen:
        #         pyautogui.hotkey('ctrl', 'p')   # PowerPoint pen mode
        #     if not self.is_drawing:
        #         pyautogui.mouseDown(button='left')
        #         self.is_drawing = True
        #     cursor.move_cursor(idx_x, idx_y, self.cam_width, self.cam_height)
        #     return "DOODLING", False

        # CURSOR — Index only
        elif hand_fingers == [0, 1, 0, 0, 0]:
            if self.is_drawing:
                pyautogui.mouseUp()
                self.is_drawing = False
            cursor.move_cursor(idx_x, idx_y, self.cam_width, self.cam_height)
            return "CURSOR", False

        # UNDO — Open palm
        # elif hand_fingers == [1, 1, 1, 1, 1]:
        #     if now - self.last_undo > self.cooldown:
        #         pyautogui.hotkey('ctrl', 'z')
        #         self.last_undo = now
        #     return "UNDO", False

        # Anything else → stop drawing
        # if self.is_drawing:
        #     pyautogui.mouseUp()
        #     self.is_drawing = False

        return "SHOW HAND", False


# UI helpers
def draw_status(img, text, pos=(60, 90)):
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_DUPLEX, 1.6, (0, 0, 0), 6, cv2.LINE_AA)
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_DUPLEX, 1.6, (0, 255, 255), 3, cv2.LINE_AA)

def draw_active_zone(img, reduction=120):
    h, w = img.shape[:2]
    cv2.rectangle(img, (reduction, reduction), (w-reduction, h-reduction), (0, 255, 255), 4)

class FPSCounter:
    def __init__(self):
        self.prev = time.time()
        self.fps = 0

    def update(self):
        now = time.time()
        self.fps = round(1 / (now - self.prev), 1)
        self.prev = now
        return self.fps

    def draw(self, img, pos=(20, 50)):
        cv2.putText(img, f'FPS: {self.fps}', pos, cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)