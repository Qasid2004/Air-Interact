# volume.py - Smooth Absolute Volume via Palm Tilt (-90° to +90° → 0% to 100%)

import time
import platform
import pyautogui  # Always for fallback

# Global flags/vars
ABSOLUTE_VOLUME = True  # Start assuming it works
_volume_interface = None
_last_volume_time = 0
_last_set_vol = -1     # For fallback tracking

try:
    if platform.system() == 'Windows':
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        from ctypes import cast, POINTER
except ImportError:
    ABSOLUTE_VOLUME = False

# Settings
VOLUME_STEP = 5            # % increments (or steps for fallback)
VOLUME_COOLDOWN = 0.15     # seconds between sets

def _get_volume_interface():
    global ABSOLUTE_VOLUME, _volume_interface
    if _volume_interface is None and ABSOLUTE_VOLUME:
        try:
            devices = AudioUtilities.GetSpeakers()
            try:
                # Standard way for IMMDevice
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                _volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
            except AttributeError:
                # Workaround if it's AudioDevice (e.g., version/wrapper issue)
                if hasattr(devices, 'EndpointVolume'):
                    _volume_interface = devices.EndpointVolume
                else:
                    raise
        except Exception as e:
            print(f"pycaw init error: {e} - Falling back to relative volume control")
            ABSOLUTE_VOLUME = False
    return _volume_interface

def set_volume(percent):
    """
    Set volume to percent (0-100). Tries absolute, falls back to relative.
    Returns True if set, False if skipped/error.
    """
    global ABSOLUTE_VOLUME, _last_volume_time, _last_set_vol
    if not 0 <= percent <= 100:
        return False

    now = time.time()
    if now - _last_volume_time < VOLUME_COOLDOWN:
        return False
    _last_volume_time = now

    if ABSOLUTE_VOLUME:
        vol = _get_volume_interface()
        if vol:
            try:
                vol.SetMasterVolumeLevelScalar(percent / 100.0, None)
                print("Using absolute volume (pycaw)")  # Temp debug - remove later
                return True
            except Exception as e:
                print(f"pycaw runtime error: {e} - Switching to fallback")
                ABSOLUTE_VOLUME = False

    # Fallback: Relative adjust with pyautogui (approximate) - improved to multi-press for larger deltas
    print("Using fallback relative volume")  # Temp debug - remove later
    if _last_set_vol == -1:
        _last_set_vol = 50  # Assume mid if unknown
    delta = percent - _last_set_vol
    if abs(delta) < VOLUME_STEP:
        return False
    num_presses = abs(delta) // 2  # ~2% per press; press multiple for bigger jumps
    key = "volumeup" if delta > 0 else "volumedown"
    for _ in range(num_presses):
        pyautogui.press(key)
    _last_set_vol += num_presses * 2 * (1 if delta > 0 else -1)
    return True