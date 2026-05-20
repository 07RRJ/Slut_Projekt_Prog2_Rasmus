from logic import data_base
from threading import Thread
from time import time

def Start(db):
    # print(db.GetTable("gamemanager"))
    db.InsertData("gamemanager", {"player": "yes"})
    print(db.GetTable("gamemanager"))

class Init:
    progress = 100
    done = 100
    db = None
    # kB = None
init = Init()

def load():
    init.db = data_base.Database()

if __name__ == "__main__":
    init = Init()
    gathering = Thread(target=load)
    gathering.start()
    gathering.join()
    db = init.db
    Start(db)