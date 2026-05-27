from threading import Thread
from data_base.supabase_client import Database
from auth.session import LoadSession
from scenes.loading_scene import LoadingScreen
from scenes.menu_scene import MainMenu
from ui.assets import Assets

class Data:
    db: Database = None
    session: dict = None
    assets: Assets = None

data = Data()

def Load():
    data.db = Database()
    data.session = LoadSession()
    data.assets = Assets()

class Game:
    def __init__(self):
        pass
    def Run(AnArgumentThatShouldntExistBecauseSomehowThisNeedsThisBecauseItDoesntGetAnArgumentButItDoesAndWithoutThisItCantFixItself=None):
        t = Thread(target=Load)
        t.start()
        LoadingScreen()
        t.join()
        MainMenu(data)