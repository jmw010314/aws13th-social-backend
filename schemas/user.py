from pydantic import BaseModel, Field, validator
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    name: str
    password: str = Field(..., min_length=8)
    nickname: str | None = None
    profile_image: str | None = None

    @validator('password')
    def check_password(cls, v):
        has_upper = any(c.isupper() for c in v)  #대문자 확인
        has_special = any(c in "!@#$%^&*" for c in v)  #특수 기호 확인

        if not has_upper or not has_special:      #둘중 한개라도 없으면 에러 메세지를 한번에 출력
            raise ValueError("대문자나 특수기호가 없습니다.")
        return v

class UserResponse(BaseModel):
    userId: str
    name: str
    email: str
    nickname: str | None
    profile_image: str | None
    created_at: datetime

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    nickname: str | None = None
    profile_image: str | None = None
    password: str | None = None