import bcrypt
from auth.session import SaveSession, ClearSession

def PromtLogin(data) -> bool:
    print("\n1) Login  2) Register  3) Exit")
    choice = input("> ").strip()

    if choice == "1":
        username = input("Username: ").strip()
        user = data.db.Login(username)
        if not user:
            print("User not found.")
            return False
        pw = input("Password: ").encode()
        if bcrypt.checkpw(pw, user["password_hash"].encode()):
            data.session = {"user_id": user["id"], "username": user["username"]}
            SaveSession(user["id"], user["username"])
            print(f"Welcome back, {username}!")
            return True
        print("Wrong password")
        return False

    elif choice == "2":
        username = input("Choose username: ").strip()
        pw = input("Choose password: ").encode()
        hashed = bcrypt.hashpw(pw, bcrypt.gensalt()).decode()
        user = data.db.Register(username, hashed)
        if user:
            data.session = {"user_id": user["id"], "username": user["username"]}
            SaveSession(user["id"], user["username"])
            print(f"Account created! Welcome, {username}!")
            return True
        print("username already taken.")
        return False

    return False

def MainMenu(data):
    if not data.session:
        if not PromtLogin(data):
            return

    print(f"\n=== Main Menu === ({data.session['username']})")
    print("1) Find Game  2) Logout  3) Exit")
    choice = input("> ").strip()

    if choice == "1":
        from logic.match_making import FindGame
        FindGame(data)
    elif choice == "2":
        ClearSession()
        data.session = None
        MainMenu(data)