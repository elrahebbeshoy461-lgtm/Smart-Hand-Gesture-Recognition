
# ==========================================================
# Gesture Controller
# ==========================================================

import ctypes
import time
from collections import deque

import pyautogui

from config import (
    ACTIONS,
    APP_OVERRIDES,
    COOLDOWN,
    SWIPE_THRESHOLD,
    SWIPE_WINDOW,
    FIST_HOLD_FRAMES,
    VOLUME_HAND,
    VOLUME_ENGAGE_FRAMES,
    VOLUME_RELEASE_FRAMES,
    VOLUME_DEADZONE,
    VOLUME_GAIN,
)

from system_volume import SystemVolume


# Disable PyAutoGUI's default delay after each action.
pyautogui.PAUSE = 0


# ==========================================================
# Get Active Window
# ==========================================================

def get_active_window_title():
    """Return the title of the currently active Windows window."""

    try:
        user32 = ctypes.windll.user32

        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)

        buffer = ctypes.create_unicode_buffer(length + 1)

        user32.GetWindowTextW(
            hwnd,
            buffer,
            length + 1,
        )

        title = buffer.value

        return title

    except Exception as error:
        print(f"[WINDOW TITLE ERROR] {error}")
        return ""


# ==========================================================
# Hand State
# ==========================================================

class HandState:
    """Store movement history and gesture state for one hand."""

    def __init__(self):
        self.history = deque()

        self.fist_frames = 0
        self.fist_latched = False


# ==========================================================
# Gesture Controller
# ==========================================================

class GestureController:
    """Connect recognized hand gestures to computer actions."""

    def __init__(self):
        self.enabled = True

        # Separate state for each hand.
        self.states = {
            "Left": HandState(),
            "Right": HandState(),
        }

        # Prevent actions from triggering too frequently.
        self.last_action_time = 0

        # System volume controller.
        self.volume = SystemVolume()

        # Volume control state.
        self.volume_active = False
        self.volume_engage_frames = 0
        self.volume_release_frames = 0

        self.volume_start_y = None
        self.volume_start_level = None

        # Prevent the same swipe from triggering repeatedly.
        self.last_swipe_time = {
            "Left": 0,
            "Right": 0,
        }

    # ======================================================
    # Normalize Hand Data
    # ======================================================

    def normalize_hand(self, hand):
        """
        Convert hand data from gui.py into the format
        expected by the controller.

        Volume control is enabled only when the index finger
        is the ONLY extended finger.

        Expected finger order:
        [thumb, index, middle, ring, pinky]
        """

        if not isinstance(hand, dict):
            return {
                "wrist": {},
                "index_up": False,
                "fist": False,
            }

        # Already normalized data.
        if "wrist" in hand:
            return hand

        landmarks = hand.get("landmarks", [])
        fingers = hand.get("fingers", [])

        gesture = str(
            hand.get("gesture", "")
        ).strip().upper()

        # --------------------------------------------------
        # Extract wrist position.
        # MediaPipe landmark 0 represents the wrist.
        # --------------------------------------------------

        wrist = {}

        if isinstance(landmarks, (list, tuple)) and landmarks:
            wrist_landmark = landmarks[0]

            if isinstance(wrist_landmark, dict):
                wrist = {
                    "x": wrist_landmark.get("x"),
                    "y": wrist_landmark.get("y"),
                }

            else:
                wrist = {
                    "x": getattr(
                        wrist_landmark,
                        "x",
                        None,
                    ),
                    "y": getattr(
                        wrist_landmark,
                        "y",
                        None,
                    ),
                }

        # --------------------------------------------------
        # Index finger ONLY.
        # --------------------------------------------------

        index_only = (
            isinstance(fingers, (list, tuple))
            and len(fingers) == 5
            and list(fingers) == [0, 1, 0, 0, 0]
        )

        # --------------------------------------------------
        # Determine whether the hand is a fist.
        # --------------------------------------------------

        is_fist = (
            gesture == "FIST"
            or "CLOSED_FIST" in gesture
        )

        return {
            "wrist": wrist,
            "index_up": index_only,
            "fist": is_fist,
        }

    # ======================================================
    # Resolve Action
    # ======================================================

    def resolve_action(self, label, event):
        """
        Resolve a gesture to its keyboard action.

        YouTube shortcuts take priority when YouTube is active.
        Other application overrides and default actions remain.
        """

        title = get_active_window_title().casefold()

        # --------------------------------------------------
        # YouTube shortcuts.
        # --------------------------------------------------

        if "youtube" in title:
            youtube_actions = {
                ("Right", "SWIPE_RIGHT"): (["l"], 1),
                ("Right", "SWIPE_LEFT"): (["j"], 1),
            }

            override = youtube_actions.get(
                (label, event)
            )

            if override is not None:
                return override

        # --------------------------------------------------
        # Other application-specific shortcuts.
        # --------------------------------------------------

        for app_text, overrides in APP_OVERRIDES.items():
            if app_text.casefold() in title:
                override = overrides.get(
                    (label, event)
                )

                if override is not None:
                    return override

        # --------------------------------------------------
        # Default action.
        # --------------------------------------------------

        return ACTIONS.get((label, event))

    # ======================================================
    # Perform Action
    # ======================================================

    def perform(self, label, event):
        """
        Execute the keyboard shortcut associated with a gesture.

        On YouTube:
            Right swipe -> L -> Forward 10 seconds.
            Left swipe  -> J -> Backward 10 seconds.

        Other gestures continue using their configured actions.
        """

        # Capture the active window title before sending keys.
        title = get_active_window_title()
        title_lower = title.casefold()

        action = self.resolve_action(label, event)

        if action is None:
            print(
                f"[ACTION] No action configured for "
                f"{label} {event}"
            )
            return None

        keys, repeat = action

        print(f"[GESTURE] {label} {event}")
        print(f"[WINDOW] {title}")
        print(f"[KEYS] {keys}")

        try:
            for _ in range(repeat):

                # ------------------------------------------
                # YouTube seeking.
                # ------------------------------------------

                if "youtube" in title_lower and label == "Right":

                    if event == "SWIPE_RIGHT":
                        pyautogui.press("l")

                        print(
                            "[YOUTUBE] Sent L - "
                            "forward 10 seconds"
                        )

                    elif event == "SWIPE_LEFT":
                        pyautogui.press("j")

                        print(
                            "[YOUTUBE] Sent J - "
                            "backward 10 seconds"
                        )

                    elif len(keys) == 1:
                        pyautogui.press(keys[0])

                    else:
                        pyautogui.hotkey(*keys)

                # ------------------------------------------
                # All other configured actions.
                # ------------------------------------------

                elif len(keys) == 1:
                    pyautogui.press(keys[0])

                else:
                    pyautogui.hotkey(*keys)

        except Exception as error:
            print(f"[ACTION ERROR] {error}")
            return None

        self.last_action_time = time.time()

        return f"{label} {event}"

    # ======================================================
    # Detect Swipe
    # ======================================================

    def detect_swipe(self, state):
        """Detect horizontal or vertical hand movement."""

        now = time.time()

        # Remove old positions outside the detection window.
        while (
            state.history
            and now - state.history[0][0] > SWIPE_WINDOW
        ):
            state.history.popleft()

        if len(state.history) < 2:
            return None

        old_time, old_x, old_y = state.history[0]
        new_time, new_x, new_y = state.history[-1]

        dx = new_x - old_x
        dy = new_y - old_y

        # --------------------------------------------------
        # Horizontal movement.
        # --------------------------------------------------

        horizontal_threshold = min(
            SWIPE_THRESHOLD,
            0.12,
        )

        if (
            abs(dx) >= horizontal_threshold
            and abs(dx) > abs(dy)
        ):
            if dx > 0:
                return "SWIPE_RIGHT"

            return "SWIPE_LEFT"

        # --------------------------------------------------
        # Vertical movement.
        # --------------------------------------------------

        if (
            abs(dy) >= SWIPE_THRESHOLD
            and abs(dy) > abs(dx)
        ):
            if dy > 0:
                return "SWIPE_DOWN"

            return "SWIPE_UP"

        return None

    # ======================================================
    # Update Volume
    # ======================================================

    def update_volume(self, hand):
        """
        Control system volume using vertical hand movement.

        Move hand upward   -> Increase volume.
        Move hand downward -> Decrease volume.
        """

        index_only = hand.get("index_up", False)

        # --------------------------------------------------
        # Index finger is not the only extended finger.
        # Stop volume control.
        # --------------------------------------------------

        if not index_only:
            self.volume_engage_frames = 0

            if self.volume_active:
                self.volume_release_frames += 1

                if (
                    self.volume_release_frames
                    >= VOLUME_RELEASE_FRAMES
                ):
                    self.volume_active = False
                    self.volume_release_frames = 0

                    self.volume_start_y = None
                    self.volume_start_level = None

            return False, None, None

        # --------------------------------------------------
        # Index finger ONLY is extended.
        # --------------------------------------------------

        self.volume_release_frames = 0
        self.volume_engage_frames += 1

        # Activate volume control after holding the gesture.
        if (
            not self.volume_active
            and self.volume_engage_frames
            >= VOLUME_ENGAGE_FRAMES
        ):
            self.volume_active = True

            wrist = hand.get("wrist", {})

            self.volume_start_y = wrist.get("y")

            try:
                self.volume_start_level = (
                    self.volume.get_volume()
                )

            except Exception as error:
                print(
                    f"[VOLUME ERROR] Could not read "
                    f"system volume: {error}"
                )

                self.volume_start_level = None

        if not self.volume_active:
            return False, None, None

        # --------------------------------------------------
        # Read current wrist position.
        # --------------------------------------------------

        wrist = hand.get("wrist", {})
        current_y = wrist.get("y")

        if (
            current_y is None
            or self.volume_start_y is None
        ):
            return True, "Volume control active", None

        # In image coordinates, smaller y means higher position.
        difference = self.volume_start_y - current_y

        # Ignore very small movements.
        if abs(difference) < VOLUME_DEADZONE:
            try:
                level = self.volume.get_volume()

            except Exception:
                level = None

            return True, "Volume control active", level

        # --------------------------------------------------
        # Calculate target volume.
        # --------------------------------------------------

        try:
            if self.volume_start_level is None:
                self.volume_start_level = (
                    self.volume.get_volume()
                )

            target_level = (
                self.volume_start_level
                + difference * VOLUME_GAIN
            )

            # Keep volume between 0% and 100%.
            target_level = max(
                0.0,
                min(1.0, target_level),
            )

            self.volume.set_volume(target_level)

            return (
                True,
                f"Volume: {int(target_level * 100)}%",
                target_level,
            )

        except Exception as error:
            print(f"[VOLUME ERROR] {error}")

            return True, "Volume control error", None

    # ======================================================
    # Process One Hand
    # ======================================================

    def process_hand(self, label, hand):
        """Process gestures detected for one hand."""

        if not self.enabled:
            return None, None

        state = self.states.get(label)

        if state is None:
            return None, None

        # --------------------------------------------------
        # Process volume control first for the selected hand.
        # --------------------------------------------------

        if label == VOLUME_HAND:
            busy, text, level = self.update_volume(hand)

            if busy:
                return text, level

        # --------------------------------------------------
        # Read wrist position.
        # --------------------------------------------------

        wrist = hand.get("wrist", {})

        x = wrist.get("x")
        y = wrist.get("y")

        if x is None or y is None:
            return None, None

        now = time.time()

        # Save current hand position.
        state.history.append((now, x, y))

        # Keep history within the detection window.
        while (
            state.history
            and now - state.history[0][0] > SWIPE_WINDOW
        ):
            state.history.popleft()

        # --------------------------------------------------
        # Fist detection.
        # --------------------------------------------------

        is_fist = hand.get("fist", False)

        if is_fist:
            state.fist_frames += 1

        else:
            state.fist_frames = 0
            state.fist_latched = False

        # Trigger only once while the fist remains closed.
        if (
            is_fist
            and state.fist_frames >= FIST_HOLD_FRAMES
            and not state.fist_latched
        ):
            state.fist_latched = True

            if (
                now - self.last_action_time
                >= COOLDOWN
            ):
                result = self.perform(
                    label,
                    "FIST",
                )

                if result:
                    return result, None

        # --------------------------------------------------
        # Swipe detection.
        # --------------------------------------------------

        event = self.detect_swipe(state)

        if (
            event
            and now - self.last_action_time >= COOLDOWN
            and now - self.last_swipe_time[label] >= COOLDOWN
        ):
            result = self.perform(
                label,
                event,
            )

            if result:
                self.last_swipe_time[label] = time.time()

                # Clear history to avoid repeating the same swipe.
                state.history.clear()

                return result, None

        return None, None

    # ======================================================
    # Update All Hands
    # ======================================================

    def update(self, hands):
        """
        Process hand data received from gui.py.

        Supports a list of hand dictionaries or a dictionary
        mapping hand labels to hand data.
        """

        if not self.enabled:
            return None, None

        normalized_hands = {}

        # --------------------------------------------------
        # Format 1: GUI sends a list.
        # --------------------------------------------------

        if isinstance(hands, list):
            for hand in hands:

                if not isinstance(hand, dict):
                    continue

                label = hand.get("label", "Unknown")

                if label not in self.states:
                    continue

                normalized_hands[label] = (
                    self.normalize_hand(hand)
                )

        # --------------------------------------------------
        # Format 2: Controller receives a dictionary.
        # --------------------------------------------------

        elif isinstance(hands, dict):
            for label, hand in hands.items():

                if label not in self.states:
                    continue

                normalized_hands[label] = (
                    self.normalize_hand(hand)
                )

        else:
            return None, None

        # --------------------------------------------------
        # No recognized hands.
        # --------------------------------------------------

        if not normalized_hands:
            return None, None

        # --------------------------------------------------
        # Process the volume-control hand first.
        # --------------------------------------------------

        if VOLUME_HAND in normalized_hands:
            text, level = self.process_hand(
                VOLUME_HAND,
                normalized_hands[VOLUME_HAND],
            )

            if text:
                return text, level

        # --------------------------------------------------
        # Process the other hand.
        # --------------------------------------------------

        for label, hand in normalized_hands.items():

            if label == VOLUME_HAND:
                continue

            text, level = self.process_hand(
                label,
                hand,
            )

            if text:
                return text, level

        return None, None

    # ======================================================
    # Toggle
    # ======================================================

    def toggle(self):
        """Enable or disable gesture control."""

        self.enabled = not self.enabled

        self.reset()

        return self.enabled

    # ======================================================
    # Reset
    # ======================================================

    def reset(self):
        """Reset hand tracking and gesture state."""

        for state in self.states.values():
            state.history.clear()

            state.fist_frames = 0
            state.fist_latched = False

        self.volume_active = False
        self.volume_engage_frames = 0
        self.volume_release_frames = 0

        self.volume_start_y = None
        self.volume_start_level = None

        self.last_action_time = 0

        self.last_swipe_time = {
            "Left": 0,
            "Right": 0,
        }

