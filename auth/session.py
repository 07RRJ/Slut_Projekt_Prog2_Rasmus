import json
from pathlib import Path
from cryptography.fernet import Fernet
from platformdirs import user_data_dir

GAME_NAME = "CardsOfRebellion"
ME = "07RRJ_Studios"

def save_path() -> Path:
    folder = Path(user_data_dir(GAME_NAME, ME))
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def key_file() -> Path:
    return save_path() / "key.bin"

def session_file() -> Path:
    return save_path() / "session.dat"

def get_or_create_key() -> bytes:
    kf = key_file()
    if kf.exists():
        return kf.read_bytes()
    key = Fernet.generate_key()
    kf.write_bytes(key)
    return key

def save_session(user_id: str, username: str) -> None:
    f = Fernet(get_or_create_key())
    data = json.dumps({"user_id": user_id, "username": username}).encode()
    session_file().write_bytes(f.encrypt(data))

def load_session() -> dict | None:
    sF = session_file()
    if not sF.exists():
        return None
    try:
        f = Fernet(get_or_create_key())
        data = f.decrypt(sF.read_bytes())
        return json.loads(data)
    except Exception:
        sF.unlink(missing_ok=True)
        return None

def clear_session() -> None:
    session_file().unlink(missing_ok=True)