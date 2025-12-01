import cv2
import mediapipe as mp
import numpy as np
import time
import logging
import os
import argparse
from gamedirectkeys import PressKey, ReleaseKey, W, A, S, D, SPACE

# ====================== NITRO COOLDOWN ======================
last_nitro_time = 0
NITRO_COOLDOWN = 1.2   # seconds between nitro activations (adjust as needed)

# Reduce OpenCV spam
logging.getLogger('cv2').setLevel(logging.ERROR)
os.environ['OPENCV_LOG_LEVEL'] = 'FATAL'

# ====================== ARGPARSER (for launcher) ======================
parser = argparse.ArgumentParser()
parser.add_argument("--cam", type=int, required=True, help="Camera index passed from launcher")
args = parser.parse_args()
CAM_IDX = args.cam

# ====================== Hand Detector ======================
class HandDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.tip_ids = [4, 8, 12, 16, 20]

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        if self.results.multi_hand_landmarks and draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def get_landmarks(self, img, hand_no=0):
        lm_list = []
        if self.results.multi_hand_landmarks and len(self.results.multi_hand_landmarks) > hand_no:
            hand = self.results.multi_hand_landmarks[hand_no]
            h, w, _ = img.shape
            for idx, lm in enumerate(hand.landmark):
                lm_list.append([idx, int(lm.x * w), int(lm.y * h)])
        return lm_list

    def get_label(self, hand_no=0):
        if (self.results.multi_handedness and 
            len(self.results.multi_handedness) > hand_no):
            return self.results.multi_handedness[hand_no].classification[0].label
        return "Unknown"

    def fingers_up(self, lm_list, label):
        if not lm_list:
            return [0] * 5
        fingers = []

        # Thumb
        if label == "Right":
            fingers.append(1 if lm_list[4][1] > lm_list[3][1] else 0)
        else:
            fingers.append(1 if lm_list[4][1] < lm_list[3][1] else 0)

        # Other four
        for i in range(1, 5):
            tip = self.tip_ids[i]
            pip = tip - 2
            fingers.append(1 if lm_list[tip][2] < lm_list[pip][2] else 0)

        return fingers

    def get_wheel_angle(self, lm1, lm2):
        if len(lm1) == 0 or len(lm2) == 0:
            return 0
        p1 = np.array([lm1[0][1], lm1[0][2]])
        p2 = np.array([lm2[0][1], lm2[0][2]])
        vec = p2 - p1
        return np.degrees(np.arctan2(vec[1], vec[0]))

# ====================== Helper ======================
def is_fist_relaxed(fingers):
    return fingers[1] == 0 and fingers[2] == 0 and sum(fingers[1:]) <= 2

# ====================== CAMERA INIT (launcher controlled) ======================
cap = cv2.VideoCapture(CAM_IDX, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print(f"\n=== AirInteract Game Mode Started (Camera {CAM_IDX}) ===\n")

detector = HandDetector()
smoothed_angle = 0
SMOOTHING = 0.75
STEER_THRESHOLD = 10


# ====================== Main Loop ======================
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera lost, reconnecting...")
            cap.release()
            time.sleep(1)
            cap = cv2.VideoCapture(CAM_IDX, cv2.CAP_DSHOW)
            continue

        frame = cv2.resize(frame, (640, 480))
        frame = cv2.flip(frame, 1)
        frame = detector.find_hands(frame)
        display = frame.copy()

        # Release all keys each frame
        for k in [W, A, D, S, SPACE]:
            ReleaseKey(k)

        hand_count = len(detector.results.multi_hand_landmarks) if detector.results.multi_hand_landmarks else 0
        cv2.putText(display, f"HANDS: {hand_count}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        if hand_count == 2:
            lm1 = detector.get_landmarks(frame, 0)
            lm2 = detector.get_landmarks(frame, 1)

            if lm1 and lm2:
                # Ensure left hand has smaller x
                if lm1[0][1] > lm2[0][1]:
                    lm1, lm2 = lm2, lm1

                fingers_L = detector.fingers_up(lm1, "Left")
                fingers_R = detector.fingers_up(lm2, "Right")

                thumb_L = fingers_L[0]
                thumb_R = fingers_R[0]
                left_fist = is_fist_relaxed(fingers_L)
                right_fist = is_fist_relaxed(fingers_R)

                # === Steering ===
                angle = detector.get_wheel_angle(lm1, lm2)
                smoothed_angle = SMOOTHING * smoothed_angle + (1 - SMOOTHING) * angle

                if smoothed_angle < -STEER_THRESHOLD:
                    PressKey(A)
                elif smoothed_angle > STEER_THRESHOLD:
                    PressKey(D)

                # Steering wheel visualization
                wrist1 = (lm1[0][1], lm1[0][2])
                wrist2 = (lm2[0][1], lm2[0][2])
                cv2.line(display, wrist1, wrist2, (255, 100, 0), 6)
                center = ((wrist1[0] + wrist2[0]) // 2, (wrist1[1] + wrist2[1]) // 2)
                cv2.circle(display, center, 70, (0, 255, 255), 4)

                # === Gestures ===
                if thumb_L and thumb_R:
                    current_time = time.time()
                    if current_time - last_nitro_time > NITRO_COOLDOWN:
                        PressKey(SPACE)
                        ReleaseKey(SPACE)          # Single clean tap
                        last_nitro_time = current_time
                        cv2.putText(display, "NITRO!!!", (160, 240),
                                    cv2.FONT_HERSHEY_DUPLEX, 2.8, (0, 255, 255), 6)
                    # ← No "NITRO READY" text when on cooldown

                elif thumb_L and right_fist:
                    PressKey(S)
                    cv2.putText(display, "BRAKE", (200, 240),
                                cv2.FONT_HERSHEY_DUPLEX, 2.2, (0, 0, 255), 5)

                elif thumb_R and left_fist:
                    cv2.putText(display, "COASTING", (160, 240),
                                cv2.FONT_HERSHEY_DUPLEX, 1.8, (255, 255, 0), 4)

                elif left_fist and right_fist:
                    PressKey(W)
                    cv2.putText(display, "GAS!", (220, 240),
                                cv2.FONT_HERSHEY_DUPLEX, 2.2, (0, 255, 0), 5)

                else:
                    cv2.putText(display, "???", (260, 240),
                                cv2.FONT_HERSHEY_DUPLEX, 2, (100, 100, 255), 4)

                cv2.putText(display, f"Steer: {smoothed_angle:+.1f}", (10, 470),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 100), 2)

            else:
                cv2.putText(display, "LANDMARKS MISSING", (100, 240),
                            cv2.FONT_HERSHEY_DUPLEX, 1.4, (0, 0, 255), 3)

        else:
            cv2.putText(display, "SHOW BOTH HANDS", (100, 240),
                        cv2.FONT_HERSHEY_DUPLEX, 1.6, (0, 0, 255), 4)

        cv2.imshow("AirInteract Game Mode - Racing Control", display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    for k in [W, A, D, S, SPACE]:
        ReleaseKey(k)
    cap.release()
    cv2.destroyAllWindows()
    print("\nAirInteract Game Mode stopped.\n")
