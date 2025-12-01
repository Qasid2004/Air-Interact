
import sys
import os
import subprocess
import time
import cv2
from PyQt6 import QtWidgets, QtCore, QtGui

# --- Configuration ---
APP_TITLE = "AirInteract Hub"
CAM_SCAN_MAX = 6
MODES = {
    "General": os.path.join("general_mode", "general_main.py"),
    "Game": os.path.join("game_mode", "game_main.py"),
    "Presentation": os.path.join("presentation_mode", "presentation_main.py"),
}

# --- Stylesheet (The "Look and Feel") ---
STYLESHEET = """
/* Main Window Background */
QMainWindow {
    background-color: #121212;
}

/* Generic Labels */
QLabel {
    color: #e0e0e0;
    font-family: "Segoe UI", "Roboto", sans-serif;
    font-size: 14px;
}

/* Headings */
QLabel#TitleLabel {
    font-size: 24px;
    font-weight: bold;
    color: #00a8ff; 
    letter-spacing: 2px;
    margin-bottom: 10px;
}

QLabel#SectionHeader {
    font-size: 12px;
    font-weight: bold;
    color: #7f8c8d;
    text-transform: uppercase;
    letter-spacing: 1px;
}

QLabel#StatusLabel {
    font-weight: bold;
    color: #bdc3c7;
    padding: 5px;
}

/* Frames/Containers */
QFrame#Card {
    background-color: #1e1e1e;
    border-radius: 10px;
    border: 1px solid #333;
}

/* ComboBox (Camera Selector) */
QComboBox {
    background-color: #2c2c2c;
    color: white;
    border: 1px solid #444;
    border-radius: 5px;
    padding: 8px;
    font-size: 13px;
}
QComboBox::drop-down {
    border: 0px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #00a8ff;
    margin-right: 10px;
}
QComboBox:on {
    border: 1px solid #00a8ff;
}

/* Buttons - General */
QPushButton {
    background-color: #2c2c2c;
    color: white;
    border-radius: 5px;
    padding: 8px 16px;
    font-weight: bold;
    border: 1px solid #444;
}
QPushButton:hover {
    background-color: #3a3a3a;
    border: 1px solid #555;
}
QPushButton:pressed {
    background-color: #1a1a1a;
}

/* Refresh Button (Small) */
QPushButton#RefreshBtn {
    background-color: transparent;
    color: #00a8ff;
    border: 1px solid #00a8ff;
}
QPushButton#RefreshBtn:hover {
    background-color: rgba(0, 168, 255, 0.1);
}

/* Mode Buttons (The Big Cards) */
QPushButton.ModeBtn {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #093545, stop:1 #1e1e1e);
    color: #ecf0f1;
    border: 1px solid #2980b9;
    border-radius: 12px;
    font-size: 16px;
    text-align: left;
    padding: 20px;
}
QPushButton.ModeBtn:hover {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #00a8ff, stop:1 #004e92);
    border: 1px solid #00d2ff;
    color: white;
}
QPushButton.ModeBtn:pressed {
    background-color: #004e92;
}

/* Stop Button (Red Theme) */
QPushButton#StopBtn {
    background-color: rgba(192, 57, 43, 0.2);
    color: #e74c3c;
    border: 1px solid #c0392b;
    font-size: 14px;
    border-radius: 8px;
    padding: 12px;
}
QPushButton#StopBtn:hover {
    background-color: #c0392b;
    color: white;
}
QPushButton#StopBtn:disabled {
    background-color: #2c2c2c;
    color: #555;
    border: 1px solid #333;
}

/* Log Terminal */
QPlainTextEdit {
    background-color: #000000;
    color: #00ff41; /* Matrix Green text */
    border: 1px solid #333;
    border-radius: 5px;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 12px;
    selection-background-color: #00a8ff;
}
/* Scrollbar Styling */
QScrollBar:vertical {
    border: none;
    background: #121212;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #444;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

def list_cameras(max_test=CAM_SCAN_MAX):
    """Helper to find available cameras."""
    cams = []
    # Use a slightly faster approach for UI responsiveness check if needed, 
    # but here we keep the logic simple as requested.
    for i in range(max_test):
        try:
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if os.name == 'nt' else i)
            if not cap.isOpened():
                cap.release()
                continue
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                cams.append((i, f"CAM {i}  |  {w}x{h} Resolution"))
            cap.release()
        except:
            pass
    return cams

class LauncherWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(600, 650)
        self.setStyleSheet(STYLESHEET)
        
        self.process = None
        self.process_mode = None

        self._build_ui()
        self._populate_cameras()
        self._setup_timer()

    def _build_ui(self):
        # Main central widget
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        
        # Main Layout
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)

        # 1. Title Header
        title = QtWidgets.QLabel(APP_TITLE.upper())
        title.setObjectName("TitleLabel")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # 2. Camera Selection Card
        cam_frame = QtWidgets.QFrame()
        cam_frame.setObjectName("Card")
        cam_layout = QtWidgets.QVBoxLayout(cam_frame)
        
        lbl_cam = QtWidgets.QLabel("VIDEO SOURCE INPUT")
        lbl_cam.setObjectName("SectionHeader")
        cam_layout.addWidget(lbl_cam)

        h_cam = QtWidgets.QHBoxLayout()
        self.cam_combo = QtWidgets.QComboBox()
        self.cam_combo.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        h_cam.addWidget(self.cam_combo, 1) # Stretch factor 1

        self.refresh_btn = QtWidgets.QPushButton("REFRESH")
        self.refresh_btn.setObjectName("RefreshBtn")
        self.refresh_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._populate_cameras)
        h_cam.addWidget(self.refresh_btn)

        cam_layout.addLayout(h_cam)
        main_layout.addWidget(cam_frame)

        # 3. Mode Selection Grid
        lbl_modes = QtWidgets.QLabel("OPERATION MODES")
        lbl_modes.setObjectName("SectionHeader")
        main_layout.addWidget(lbl_modes)

        grid_layout = QtWidgets.QGridLayout()
        grid_layout.setSpacing(15)

        # Button: General
        self.btn_general = QtWidgets.QPushButton("GENERAL\nMODE")
        self.btn_general.setProperty("class", "ModeBtn") # For CSS selection
        self.btn_general.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.btn_general.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.btn_general.clicked.connect(lambda: self.start_mode("General"))
        grid_layout.addWidget(self.btn_general, 0, 0)

        # Button: Game
        self.btn_game = QtWidgets.QPushButton("GAME\nMODE")
        self.btn_game.setProperty("class", "ModeBtn")
        self.btn_game.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.btn_game.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.btn_game.clicked.connect(lambda: self.start_mode("Game"))
        grid_layout.addWidget(self.btn_game, 0, 1)

        # Button: Presentation (Full Width)
        self.btn_presentation = QtWidgets.QPushButton("PRESENTATION\nMODE")
        self.btn_presentation.setProperty("class", "ModeBtn")
        self.btn_presentation.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.btn_presentation.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.btn_presentation.clicked.connect(lambda: self.start_mode("Presentation"))
        grid_layout.addWidget(self.btn_presentation, 1, 0, 1, 2)

        # Allow grid to take up available space
        main_layout.addLayout(grid_layout, 1) 

        # 4. Status & Controls
        control_frame = QtWidgets.QFrame()
        control_frame.setObjectName("Card")
        control_layout = QtWidgets.QVBoxLayout(control_frame)

        status_row = QtWidgets.QHBoxLayout()
        
        self.status_label = QtWidgets.QLabel("SYSTEM IDLE")
        self.status_label.setObjectName("StatusLabel")
        status_row.addWidget(self.status_label, 1)

        self.stop_btn = QtWidgets.QPushButton("TERMINATE ACTIVE MODE")
        self.stop_btn.setObjectName("StopBtn")
        self.stop_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.stop_mode)
        self.stop_btn.setEnabled(False) # Disabled initially
        status_row.addWidget(self.stop_btn)

        control_layout.addLayout(status_row)
        main_layout.addWidget(control_frame)

        # 5. Console Log
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        self.log.setPlaceholderText("System logs will appear here...")
        main_layout.addWidget(self.log)

    def _log(self, msg):
        ts = time.strftime("%H:%M:%S")
        # Using HTML for color in logs
        self.log.appendHtml(f"<span style='color: #555;'>[{ts}]</span> <span style='color: #00ff41;'>{msg}</span>")
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def _populate_cameras(self):
        current_idx = self.cam_combo.currentData()
        self.cam_combo.clear()
        self._log("Scanning for video devices...")
        
        # Process events to let UI redraw before scan (scan can be slow)
        QtWidgets.QApplication.processEvents()
        
        cams = list_cameras()
        if not cams:
            self.cam_combo.addItem("No cameras detected", -1)
            self._log("Error: No cameras found.")
            return
        
        for idx, label in cams:
            self.cam_combo.addItem(label, idx)
        
        self._log(f"Scan complete. {len(cams)} device(s) found.")
        
        # Restore selection if it still exists
        if current_idx is not None:
            index = self.cam_combo.findData(current_idx)
            if index >= 0:
                self.cam_combo.setCurrentIndex(index)
            else:
                self.cam_combo.setCurrentIndex(0)
        else:
            self.cam_combo.setCurrentIndex(0)

    def _update_ui_state(self, running):
        """Toggles buttons based on state"""
        # Disable mode buttons if running
        self.btn_general.setEnabled(not running)
        self.btn_game.setEnabled(not running)
        self.btn_presentation.setEnabled(not running)
        self.cam_combo.setEnabled(not running)
        self.refresh_btn.setEnabled(not running)
        
        # Enable stop button if running
        self.stop_btn.setEnabled(running)
        
        if running:
            self.status_label.setText(f"ACTIVE: {self.process_mode.upper()}")
            self.status_label.setStyleSheet("color: #00a8ff;")
        else:
            self.status_label.setText("SYSTEM IDLE")
            self.status_label.setStyleSheet("color: #bdc3c7;")

    def start_mode(self, mode_name):
        if mode_name not in MODES:
            self._log(f"Unknown mode: {mode_name}")
            return
            
        cam_index = self.cam_combo.currentData()
        if cam_index is None or cam_index == -1:
            QtWidgets.QMessageBox.warning(self, "No Camera", "Please select a valid camera source.")
            return

        # If same mode running
        if self.process and self.process_mode == mode_name and self.process.poll() is None:
            return

        # Stop existing
        if self.process:
            self._terminate_process()

        self._log(f"Initializing {mode_name}...")
        QtCore.QCoreApplication.processEvents()
        
        # Small visual delay for "feel"
        time.sleep(0.2) 

        script_rel = MODES[mode_name]
        script_path = os.path.join(os.getcwd(), script_rel)
        
        if not os.path.isfile(script_path):
            QtWidgets.QMessageBox.critical(self, "Script Missing", f"Cannot find:\n{script_path}")
            self._log(f"Error: Script missing at {script_path}")
            return

        cmd = [sys.executable, script_path, "--cam", str(int(cam_index))]
        self._log(f"Executing: {' '.join(cmd)}")
        
        try:
            self.process = subprocess.Popen(cmd, cwd=os.getcwd())
            self.process_mode = mode_name
            self._update_ui_state(True)
            self._log(f"Process started (PID: {self.process.pid})")
        except Exception as e:
            self._log(f"Launch failed: {e}")
            QtWidgets.QMessageBox.critical(self, "Start Failed", str(e))
            self.process = None
            self.process_mode = None
            self._update_ui_state(False)

    def _terminate_process(self):
        if not self.process:
            return
        try:
            self._log("Sending terminate signal...")
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
                self._log("Process terminated gracefully.")
            except subprocess.TimeoutExpired:
                self._log("Process unresponsive. Force killing...")
                self.process.kill()
                self.process.wait(timeout=2)
                self._log("Process killed.")
        except Exception as e:
            self._log(f"Error during termination: {e}")
        finally:
            self.process = None
            self.process_mode = None
            self._update_ui_state(False)

    def stop_mode(self):
        if not self.process:
            return
        self._terminate_process()

    def _setup_timer(self):
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self._poll_process)
        self.timer.start()

    def _poll_process(self):
        if self.process:
            ret = self.process.poll()
            if ret is not None:
                self._log(f"Mode '{self.process_mode}' ended (Code: {ret})")
                self.process = None
                self.process_mode = None
                self._update_ui_state(False)
                
                # Visual feedback on crash/exit
                if ret != 0 and ret != 1: # 1 is often manual exit, others are crash
                     QtWidgets.QMessageBox.warning(self, "Process Exited", f"The subprocess exited with code {ret}.")

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Set generic font for the app
    font = QtGui.QFont("Segoe UI", 10)
    app.setFont(font)
    
    win = LauncherWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()