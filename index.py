from threading import Thread
from logic.data_base import Database
from auth.session import LoadSession
from ui.loading import LoadingScreen
from ui.menu import MainMenu
from ui.assets import Assets

class Data:
    db: Database = None
    session: dict = None
    assets: Assets = None

data = Data()

def _load():
    data.db = Database()
    data.session = LoadSession()
    data.assets = Assets()

if __name__ == "__main__":
    t = Thread(target=_load)
    t.start()
    LoadingScreen()
    t.join()
    MainMenu(data)