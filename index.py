from threading import Thread
from logic.data_base import Database
from auth.session import load_session
from ui.loading import LoadingScreen
from ui.menu import MainMenu

class App:
    db: Database = None
    session: dict = None

app = App()

def _load():
    app.db = Database()
    app.session = load_session()

if __name__ == "__main__":
    t = Thread(target=_load)
    t.start()
    LoadingScreen()
    t.join()
    MainMenu(app)