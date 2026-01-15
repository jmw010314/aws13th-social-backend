from fastapi import APIRouter, HTTPException
from schemas.user import UserLogin
from utils.auth import verify_password, create_access_token
from utils.data import load_data

router = APIRouter(prefix="/auth",tags=["Auth"])

@router.post("/tokens")
def login(data: UserLogin):
    users = load_data("users")
    matched_user = None

    for user in users:
        if user["email"].lower() == data.email.lower():
            matched_user = user
            break

    if matched_user and verify_password(data.password, matched_user["password"]):
        access_token = create_access_token(
            data={"sub": matched_user["userId"]}
        )
        return{
            "status": "success",
            "data":{
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 3600,
             }
        }

    raise HTTPException(
        status_code=401,
        detail={
            "status": "error",
            "data": {
                "message": "이메일 또는 비밀번호가 일치하지 않습니다."
            }
        }
    )
