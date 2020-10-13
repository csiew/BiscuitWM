from window_manager import WindowManager
from session_info import SessionInfo
from preferences import Preferences

if __name__ == "__main__":
    WindowManager(prefs=Preferences(), session_info=SessionInfo()).main()
