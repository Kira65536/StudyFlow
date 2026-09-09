from  pwdlib import PasswordHash

#объект с настройками
password_hash = PasswordHash.recommended()
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