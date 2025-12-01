# presentation_main.py - FINAL PROFESSIONAL VERSION

import cv2
import pyautogui
import argparse
import time
from presentation_gestures import handDetector, GestureManager, draw_status, draw_active_zone, FPSCounter
import ctypes
import sys


def change_cursor_to_hand():
    try:
        # Try the direct method first
        hcursor = ctypes.windll.user32.LoadCursorW(0, 32649)  # IDC_HAND
        ctypes.windll.user32.SetSystemCursor(hcursor, 32512)
        print("Cursor → Hand")
    except:
        try:
            # Fallback method
            ctypes.windll.user32.LoadCursorW.restype = ctypes.c_void_p
            hcursor = ctypes.windll.user32.LoadCursorW(0, 32649)
            ctypes.windll.user32.SetSystemCursor(hcursor, 32512)
            print("Cursor → Hand (fallback)")
        except:
            print("Could not change cursor – using default")

def restore_cursor():
    try:
        ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 0)
        print("Cursor restored")
    except:
        pass

# Call at start
change_cursor_to_hand()

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

parser = argparse.ArgumentParser()
parser.add_argument("--cam", type=int, required=True)
args = parser.parse_args()

cap = cv2.VideoCapture(args.cam, cv2.CAP_DSHOW)
cap.set(3, 640)
cap.set(4, 480)

detector = handDetector()
manager = GestureManager()
fps = FPSCounter()

print("\nAIR PRESENTATION CONTROLLER READY!")
print("Thumb → Next | Fist → Prev | Index+Middle → Draw | Open Palm → Undo\n")

while True:
    ret, img = cap.read()
    if not ret: break
    img = cv2.flip(img, 1)

    img = detector.findHands(img)
    lmlist_l = lmlist_r = fingers_l = fingers_r = None

    if detector.results.multi_hand_landmarks:
        for i in range(len(detector.results.multi_hand_landmarks)):
            lm = detector.findPosition(img, i)
            fingers = detector.fingersUp(lm)
            hand = detector.getHandedness(i)
            if hand == "Left":
                lmlist_l, fingers_l = lm, fingers
            else:
                lmlist_r, fingers_r = lm, fingers

    status, _ = manager.process_gesture(lmlist_l, lmlist_r, fingers_l, fingers_r)

    draw_active_zone(img)
    draw_status(img, status)
    fps.draw(img)

    cv2.imshow("AirInteract - Presentation Controller", img)
    if cv2.waitKey(1) == 27:  # ESC
        if manager.is_drawing:
            pyautogui.mouseUp()
        break

cap.release()
cv2.destroyAllWindows()

# Call at end
restore_cursor()

print("Goodbye!")