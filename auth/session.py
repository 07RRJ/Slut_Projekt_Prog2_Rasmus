import json
from pathlib import Path
from cryptography.fernet import Fernet
from platformdirs import user_data_dir

GAME_NAME = "CardsOfRebelion"
ME = "07RRJ_Studios"

def SavePath() -> Path:
    folder = Path(user_data_dir(GAME_NAME, ME))
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def KeyFile() -> Path:
    return SavePath() / "key.bin"

def SessionFile() -> Path:
    return SavePath() / "session.dat"

def GetOrCreateKey() -> bytes:
    kf = KeyFile()
    if kf.exists():
        return kf.read_bytes()
    key = Fernet.generate_key()
    kf.write_bytes(key)
    return key

def SaveSession(userId: str, userName: str) -> None:
    f = Fernet(GetOrCreateKey())
    data = json.dumps({"userId": userId, "username": userName}).encode()
    SessionFile().write_bytes(f.encrypt(data))

def load_session() -> dict | None:
    sF = SessionFile()
    if not sF.exists():
        return None
    try:
        f = Fernet(GetOrCreateKey())
        data = f.decrypt(sF.read_bytes())
        return json.loads(data)
    except Exception:
        sF.unlink(missing_ok=True)
        return None

def clear_session() -> None:
    SessionFile().unlink(missing_ok=True)