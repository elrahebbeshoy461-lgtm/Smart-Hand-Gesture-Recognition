
import pyautogui

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    PYCAW_OK = True

except Exception:
    PYCAW_OK = False


class SystemVolume:
    """Controls Windows master volume from 0.0 to 1.0."""

    def __init__(self):
        self.endpoint = None
        self.fallback_level = 0.5

        if not PYCAW_OK:
            print(
                "pycaw is not available; "
                "using volume keys as fallback."
            )
            return

        try:
            device = AudioUtilities.GetSpeakers()

            if hasattr(device, "EndpointVolume"):
                self.endpoint = device.EndpointVolume

            else:
                interface = device.Activate(
                    IAudioEndpointVolume._iid_,
                    CLSCTX_ALL,
                    None
                )

                self.endpoint = cast(
                    interface,
                    POINTER(IAudioEndpointVolume)
                )

            # Read the actual Windows volume when possible.
            self.fallback_level = float(
                self.endpoint.GetMasterVolumeLevelScalar()
            )

        except Exception as error:
            self.endpoint = None
            print("Cannot initialize Windows audio:", error)

    def get_volume(self):
        """Return the current volume between 0.0 and 1.0."""

        if self.endpoint is not None:
            try:
                self.fallback_level = float(
                    self.endpoint.GetMasterVolumeLevelScalar()
                )
            except Exception as error:
                print("Could not read system volume:", error)

        return self.fallback_level

    def set_volume(self, level):
        """Set the master volume between 0.0 and 1.0."""

        level = max(0.0, min(1.0, float(level)))

        if self.endpoint is not None:
            try:
                self.endpoint.SetMasterVolumeLevelScalar(
                    level,
                    None
                )

                self.fallback_level = level
                return True

            except Exception as error:
                print("Could not set system volume:", error)

        # Fallback: use Windows volume keys.
        current = self.fallback_level
        difference = level - current

        # Approximate each key press as a 2% change.
        presses = int(round(abs(difference) / 0.02))

        if presses > 0:
            key = "volumeup" if difference > 0 else "volumedown"

            try:
                pyautogui.press(key, presses=presses)
            except Exception as error:
                print("Could not change volume using keys:", error)
                return False

        # This is only an estimate when pycaw is unavailable.
        self.fallback_level = level
        return True

    # Compatibility with code that uses get() and set().
    def get(self):
        return self.get_volume()

    def set(self, level):
        return self.set_volume(level)
