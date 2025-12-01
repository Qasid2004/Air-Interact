# handtracking.py - Enhanced & Mirror-Safe (Palm-Facing-Camera Priority)

import cv2
import mediapipe as mp
import math

class handDetector:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.7, trackCon=0.7):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

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
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            h, w, _ = img.shape
            handedness = self.getHandedness(handNo)

            for id, lm in enumerate(myHand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                # Flip X for right hand to match left-hand logic
                if handedness == 'Right':
                    cx = w - cx
                lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 7, (255, 0, 255), cv2.FILLED)
        return lmList

    def fingersUp(self, lmList):
        if len(lmList) == 0:
            return [0, 0, 0, 0, 0]

        fingers = []

        # === PALM ORIENTATION DETECTION ===
        wrist = lmList[0][1:]      # [x, y]
        mcp_middle = lmList[9][1:] # middle finger MCP
        mcp_index = lmList[5][1:]  # index finger MCP

        vec_wrist_to_middle = (mcp_middle[0] - wrist[0], mcp_middle[1] - wrist[1])
        vec_middle_to_index = (mcp_index[0] - mcp_middle[0], mcp_index[1] - mcp_middle[1])

        cross = vec_wrist_to_middle[0] * vec_middle_to_index[1] - vec_wrist_to_middle[1] * vec_middle_to_index[0]
        palm_facing_camera = cross > 0  # True = back of hand toward camera

        # === THUMB: FLIPPED LOGIC (Optimized for palm-facing-camera) ===
        thumb_tip_x = lmList[4][1]
        thumb_mcp_x = lmList[2][1]

        if palm_facing_camera:
            # Back of hand: thumb is on the RIGHT → tip x > joint x = up
            fingers.append(1 if thumb_tip_x > thumb_mcp_x else 0)
        else:
            # Palm toward you: thumb on LEFT → tip x < joint x = up
            fingers.append(1 if thumb_tip_x < thumb_mcp_x else 0)

        # === OTHER FINGERS: Y-based (tip above PIP = up) ===
        for i in range(1, 5):
            tip_y = lmList[self.tipIds[i]][2]
            pip_y = lmList[self.tipIds[i] - 2][2]
            fingers.append(1 if tip_y < pip_y else 0)

        return fingers

    def findDistance(self, p1, p2, lmList, img=None, draw=True):
        if len(lmList) <= max(p1, p2):
            return 1000, img, []

        x1, y1 = lmList[p1][1], lmList[p1][2]
        x2, y2 = lmList[p2][1], lmList[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)

        if draw and img is not None:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

        return length, img, [x1, y1, x2, y2, cx, cy]

    def getHandedness(self, handNo=0):
        """Returns 'Left' or 'Right' safely"""
        if (self.results.multi_handedness and 
            len(self.results.multi_handedness) > handNo):
            return self.results.multi_handedness[handNo].classification[0].label
        return "Unknown"