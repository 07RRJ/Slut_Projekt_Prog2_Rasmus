import sys, os

def GetGameFolder():
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def ResourcePath(relative_path):
    return os.path.join(GetGameFolder(), relative_path)