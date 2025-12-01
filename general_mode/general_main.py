import cv2
import pyautogui
import argparse
import handtracking as htm
import utils
import gestures

# ============================
# PYAUTOGUI SETTINGS
# ============================
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# ============================
# CONFIG
# ============================
FRAME_REDUCTION = 120
CAM_WIDTH, CAM_HEIGHT = 640, 480
CLICK_COOLDOWN = 0.5

# ============================
# ARGPARSE (Launcher -> Mode)
# ============================
parser = argparse.ArgumentParser()
parser.add_argument("--cam", type=int, required=True, help="Camera index passed from launcher")
args = parser.parse_args()
CAM_IDX = args.cam

# ============================
# INITIALIZE CAMERA
# ============================
cap = cv2.VideoCapture(CAM_IDX, cv2.CAP_DSHOW)
cap.set(3, CAM_WIDTH)
cap.set(4, CAM_HEIGHT)

detector = htm.handDetector(maxHands=2, detectionCon=0.75, trackCon=0.75)
fps = utils.FPSCounter()
manager = gestures.GestureManager(CAM_WIDTH, CAM_HEIGHT, FRAME_REDUCTION, CLICK_COOLDOWN)

print("\n===============================================")
print("         AirInteract – General Mode")
print("===============================================")

# ============================
# MAIN LOOP
# ============================
while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    img = detector.findHands(img, draw=True)

    # === Separate Left & Right hands ===
    lmList_left = lmList_right = None
    fingers_left = fingers_right = None

    if detector.results.multi_hand_landmarks:
        for i, hand_lm in enumerate(detector.results.multi_hand_landmarks):
            lmList = detector.findPosition(img, handNo=i, draw=False)
            handedness = detector.getHandedness(i)
            fingers = detector.fingersUp(lmList)

            if handedness == "Left":
                lmList_left = lmList
                fingers_left = fingers
            else:
                lmList_right = lmList
                fingers_right = fingers

    # Draw active zone
    utils.draw_active_zone(img, FRAME_REDUCTION, (255, 0, 255), 3)

    # === Process Gestures ===
    status, holding_ctrl = manager.process_gesture(
        lmList_left, lmList_right, fingers_left, fingers_right
    )

    # Safely release Ctrl when not zooming
    if not holding_ctrl:
        pyautogui.keyUp('ctrl')

    # ============================
    # ON-SCREEN STATUS
    # ============================
    if status == "PINCH ZOOM":
        utils.draw_status(img, "PINCH ZOOM", (60, 80), (255, 255, 0), 3.2)
    elif status == "SCROLL ↑↓":
        utils.draw_status(img, "SCROLL ↑↓", (80, 80), (0, 255, 255), 3.0)
    elif status.startswith("VOLUME"):
        utils.draw_status(img, status, (100, 80), (0, 255, 0), 2.6)
    elif status == "DOUBLE CLICK":
        utils.draw_status(img, status, (80, 80), (0, 255, 255), 2.8)
    elif status == "RIGHT CLICK":
        utils.draw_status(img, status, (100, 80), (0, 100, 255), 2.6)
    elif status == "LEFT CLICK":
        utils.draw_status(img, status, (140, 80), (0, 255, 0), 2.6)
    elif status == "CURSOR":
        utils.draw_status(img, status, (200, 70), (255, 0, 255), 2.6)
    else:
        utils.draw_status(img, "SHOW HAND", (180, 240), (0, 0, 255), 2.2)

    # FPS + Instruction Bar
    fps.update()
    fps.draw(img)
    cv2.putText(
        img,
        "Zoom | Scroll | Volume | Cursor | Clicks",
        (10, 470),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (50, 255, 50),
        2
    )

    cv2.imshow("AirInteract – General Mode", img)
    if cv2.waitKey(1) == 27:  # ESC
        pyautogui.keyUp('ctrl')
        break

cap.release()
cv2.destroyAllWindows()
print("\nGeneral Mode Closed.\n")
