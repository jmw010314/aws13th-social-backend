from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# 해시 객체 생성
ph = PasswordHasher()

def get_password_hash(password: str) -> str:

    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:

    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
