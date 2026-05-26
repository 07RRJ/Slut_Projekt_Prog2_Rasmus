import bcrypt
from auth.session import save_session, clear_session

def _prompt_login(app) -> bool:
    print("\n1) Login  2) Register  3) Exit")
    choice = input("> ").strip()

    if choice == "1":
        userName = input("Username: ").strip()
        user = app.db.login(userName)
        if not user:
            print("User not found.")
            return False
        pw = input("Password: ").encode()
        if bcrypt.checkpw(pw, user["password_hash"].encode()):
            app.session = {"user_id": user["id"], "username": user["username"]}
            save_session(user["id"], user["username"])
            print(f"Welcome back, {userName}!")
            return True
        print("Wrong password")
        return False

    elif choice == "2":
        userName = input("Choose username: ").strip()
        pw = input("Choose password: ").encode()
        hashed = bcrypt.hashpw(pw, bcrypt.gensalt()).decode()
        user = app.db.Register(userName, hashed)
        if user:
            app.session = {"user_id": user["id"], "username": user["username"]}
            save_session(user["id"], user["username"])
            print(f"Account created! Welcome, {userName}!")
            return True
        print("Username already taken.")
        return False

    return False

def MainMenu(app):
    if not app.session:
        if not _prompt_login(app):
            return

    print(f"\n=== Main Menu === ({app.session['username']})")
    print("1) Find Game  2) Logout  3) Exit")
    choice = input("> ").strip()

    if choice == "1":
        from logic.match_making import FindGame
        FindGame(app)
    elif choice == "2":
        clear_session()
        app.session = None
        MainMenu(app)