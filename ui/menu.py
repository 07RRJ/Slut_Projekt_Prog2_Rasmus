from logic.game_loop import Start

def FindGame(db):
    print("FindGame")
    db.InsertData("gamemanager", {"player": "yes"})
    print(db.GetTable("gamemanager"))
    if True:
        Start(db)

def MainMenu(db):
    print("MainMenu")
    FindGame(db)

def LoadingScreen():
    print("LoadingScreen")