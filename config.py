from pathlib import Path

CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

MAX_HANDS = 2
DETECTION_CONFIDENCE = 0.6
TRACKING_CONFIDENCE = 0.6

WINDOW_TITLE = "Smart Hand Gesture Recognition"
FPS_SMOOTHING = 0.9
GESTURE_CONFIDENCE = 0.85

# ======================================================
# Hand Landmarker model
# ======================================================

# assets/models/hand_landmarker.task next to this file
HAND_MODEL_PATH = (
    Path(__file__).resolve().parent
    / "assets"
    / "models"
    / "hand_landmarker.task"
)

# Downloaded automatically if the file is missing
HAND_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/"
    "hand_landmarker.task"
)

# ======================================================
# Handedness
# ======================================================

# If the Left / Right label shows the wrong hand, flip this value
SWAP_HANDEDNESS = True

# ======================================================
# Gesture Control: timing
# ======================================================

# Seconds to wait between two discrete actions (fist, swipe)
COOLDOWN = 1.0

# How far the wrist must travel (fraction of the frame, 0..1)
SWIPE_THRESHOLD = 0.25

# The movement must happen within this many seconds
SWIPE_WINDOW = 0.4

# Fist must be held for this many frames to count
FIST_HOLD_FRAMES = 6

# ======================================================
# Gesture Control: volume
#
# Index finger up (other fingers folded) = volume mode.
# Move the hand up -> louder, down -> quieter.
# ======================================================

# Which hand controls the volume
VOLUME_HAND = "Right"

# Frames the posture must be held before volume mode starts
VOLUME_ENGAGE_FRAMES = 5

# Frames the posture can be lost before volume mode ends
VOLUME_RELEASE_FRAMES = 6

# Hand must move this much (fraction of frame height) to count
VOLUME_DEADZONE = 0.01

# 1.5 means: moving the hand 2/3 of the frame height = 100% volume
VOLUME_GAIN = 1.5

# ======================================================
# Gesture Control: actions
#
# (hand, event) -> (keys to press, how many times)
# Events: FIST, SWIPE_LEFT, SWIPE_RIGHT, SWIPE_UP, SWIPE_DOWN
#
# playpause / nexttrack / prevtrack / volumemute are the
# global media keys: they work in any app or browser,
# even when its window is not the active one.
# ======================================================

ACTIONS = {
    # Right hand: media
    ("Right", "FIST"):        (["playpause"], 1),
    ("Right", "SWIPE_RIGHT"): (["nexttrack"], 1),
    ("Right", "SWIPE_LEFT"):  (["prevtrack"], 1),

    # Left hand: system
    ("Left", "FIST"):         (["volumemute"], 1),
    ("Left", "SWIPE_RIGHT"):  (["alt", "tab"], 1),
    ("Left", "SWIPE_LEFT"):   (["alt", "shift", "tab"], 1),
}

# ======================================================
# Per-app overrides
#
# If the active window title contains the text (not case
# sensitive), these replace the matching entries above.
# ======================================================

APP_OVERRIDES = {
    # YouTube in a browser
    "YouTube": {
        ("Right", "SWIPE_RIGHT"): (["l"], 1),
        ("Right", "SWIPE_LEFT"): (["j"], 1),
    },

    # VLC Media Player
    "VLC": {
        ("Right", "SWIPE_RIGHT"): (["alt", "right"], 1),
        ("Right", "SWIPE_LEFT"): (["alt", "left"], 1),
    },

    # PotPlayer
    "PotPlayer": {
        ("Right", "SWIPE_RIGHT"): (["right"], 1),
        ("Right", "SWIPE_LEFT"): (["left"], 1),
    },

    # Media Player Classic Home Cinema
    "MPC-HC": {
        ("Right", "SWIPE_RIGHT"): (["right"], 1),
        ("Right", "SWIPE_LEFT"): (["left"], 1),
    },

    # Media Player Classic Black Edition
    "MPC-BE": {
        ("Right", "SWIPE_RIGHT"): (["right"], 1),
        ("Right", "SWIPE_LEFT"): (["left"], 1),
    },
}




# ======================================================
# Overlay settings
# ======================================================

OVERLAY_SECONDS = 2.0