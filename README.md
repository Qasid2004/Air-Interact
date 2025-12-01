# AirInteract Hub

**AirInteract Hub** is a Python-based application that allows you to control various programs and modes using **computer vision** and **hand gestures**. It includes **General Mode**, **Game Mode**, and **Presentation Mode** with real-time gesture detection.

## Features

- **Computer Vision & Hand Gesture Control**
  - Uses **MediaPipe** and **OpenCV** to detect hand gestures.
  - Supports cursor control, slide navigation, drawing, and undo actions in Presentation Mode.
- **Modes**
  - **General Mode** – Basic interaction and testing.
  - **Game Mode** – Gesture-based game controls.
  - **Presentation Mode** – Control PowerPoint or PDF slides with hand gestures.
- **User-Friendly GUI**
  - Developed with **PyQt6**.
  - Easy camera selection.
  - Start/Stop modes directly from the interface.
  - Console log for system messages.
- **Cross-Platform Compatible**
  - Tested on **Windows** (requires minor adjustment for Linux/Mac).

## Installation

1. Clone this repository:
  
   git clone https://github.com/Qasid2004/airinteract-hub.git
   cd airinteract-hub

Install required Python packages:

pip install -r requirements.txt

Required libraries include:

PyQt6

opencv-python

mediapipe

numpy

pyautogui

Run the launcher:

python launcher.py --cam 0


Replace 0 with your camera index.


Folder Structure
airinteract-hub/
│
├─ launcher.py           # Main GUI launcher
├─ presentation_mode/
│   ├─ presentation_main.py
│   ├─ presentation_gestures.py
│   └─ presentation_controls.py
├─ game_mode/
│   └─ game_main.py
├─ general_mode/
│   └─ general_main.py
├─ requirements.txt
└─ README.md

1. Usage / How to Use (Step-by-step)

A section explaining how to run each mode:

How to open Presentation Mode

How to open Game Mode

How to open General Mode

What gestures control what

Keyboard shortcuts

Camera troubleshooting

2. Gesture Controls Table

A clean table showing controls like:

Gesture	Action:
Thumbs left = Previous Slide
Thumbs right = Next Slide
Index Finger = Cursor Control
Index + Middle	Drawing

