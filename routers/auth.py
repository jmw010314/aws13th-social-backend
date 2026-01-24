from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from utils.auth import verify_password, create_access_token
from utils.data import load_data

router = APIRouter(prefix="/auth",tags=["Auth"])

@router.post("/tokens")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users = load_data("users")
    matched_user = None

    for user in users:
        if (user.get("email") or "").lower() == form_data.username.lower() and not user.get("is_deleted", False):
            matched_user = user
            break

    if matched_user and verify_password(form_data.password, matched_user["password"]):
        access_token = create_access_token(
            data={"sub": matched_user["userId"]}
        )
        return{
            "access_token": access_token,
            "token_type": "bearer",
             }


    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "status": "error",
            "data": {
                "message": "이메일 또는 비밀번호가 일치하지 않습니다."
            }
        }
    )