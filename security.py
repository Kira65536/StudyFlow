from  pwdlib import PasswordHash
import os
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

#объект с настройками
password_hash = PasswordHash.recommended()
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET не найден в .env")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
#превращает обычный пароль в безопасный
def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(
        plain_password: str,
        hashed_password: str
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password
    )
def create_access_token(user_id: int) -> str:

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": int(expire.timestamp())
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

def decode_access_token(token: str) -> int:

    # Расшифровываем и проверяем JWT
    payload = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM]
    )

    user_id = payload.get("sub")

    if user_id is None:
        raise ValueError("В токене отсутствует user_id")
    return int(user_id)