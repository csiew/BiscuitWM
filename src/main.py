from components.window_manager import WindowManager
from models.session_info import SessionInfo
from utils.preferences import Preferences

if __name__ == "__main__":
    WindowManager(prefs=Preferences(), session_info=SessionInfo()).main()
