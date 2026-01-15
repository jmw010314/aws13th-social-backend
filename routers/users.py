from fastapi import APIRouter, status, HTTPException, Depends
from schemas.user import UserCreate, UserUpdate
from datetime import datetime, timezone

from utils import data
from utils.auth import get_password_hash, get_current_user
from utils.data import load_data,save_data
import uuid

router = APIRouter(prefix="/users",tags=["Users"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def signup(data: UserCreate):
    users = load_data("users")


    if any(u.get('email') == data.email for u in users):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"status": "error", "data": {"message": "이미 존재하는 이메일입니다."}}
        )
    if data.nickname:
        if any(u.get('nickname', '') == data.nickname.lower() for u in users):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"status": "error","data":{"message":"닉네임이 중복되었습니다."}}
            )
    new_user = {
        "userId": str(uuid.uuid4()),
        "email": data.email,
        "name": data.name,
        "password": get_password_hash(data.password),
        "nickname": data.nickname,
        "profile_image": data.profile_image,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    users.append(new_user)
    save_data("users", users)
    return {"status": "success",
            "data":{
                "userId":new_user["userId"],
                "email":new_user["email"],
                "name":new_user["name"],
                "nickname":new_user["nickname"],
                "created_at":new_user["created_at"]
             }
            }

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "status": "success",
        "data": {
            "email": current_user["email"],
            "name": current_user.get("name"),
            "nickname": current_user.get("nickname"),
            "profile_image": current_user.get("profile_image"),
        }
    }

@router.patch("/me")
def update_me(
        data: UserUpdate,
        current_user: dict = Depends(get_current_user)
):
        users = load_data("users")

        #닉네임 중복 체크(본인은 제외)
        if data.nickname:
            for user in users:
                if(
                    user["nickname"] == data.nickname
                    and user["userId"] != current_user["userId"]
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "status": "error",
                            "data":{"message: 닉네임이 중복되었습니다."}
                        }
                    )
        #내 계정 수정
        for user in users:
            if user["userId"] == current_user["userId"]:
                if data.nickname is not None:
                    user["nickname"] = data.nickname

                if data.profile_image is not None:
                    user["profile_image"] = data.profile_image

                if data.password is not None:
                    user["password"] = get_password_hash(data.password)

                save_data("users", users)

                return {
                    "status": "success",
                    "data": {
                        "nickname": user["nickname"],
                        "profile_image": user["profile_image"],
                    }
                }



@router.delete("/me")
def delete_me():
    return {"message": "회원 탈퇴"}

@router.get("/{user_id}")
def get_user(user_id: str):
    return {"message": f"{user_id}번 회원 조회"}