from fastapi import APIRouter, status, HTTPException, Depends, Response
from schemas.user import UserCreate, UserUpdate
from datetime import datetime, timezone

from utils import data
from utils.auth import get_password_hash, get_current_user
from utils.data import load_data, save_data, find_user_by_id, soft_delete_user
import uuid

router = APIRouter(prefix="/users",tags=["Users"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def signup(data: UserCreate):
    users = load_data("users")

    for u in users:
        u.setdefault("is_deleted", False)
    active_users = [u for u in users if u.get("is_deleted") is False]

    if any(u.get('email', '').lower() == data.email.lower() for u in active_users):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"status": "error", "data": {"message": "이미 존재하는 이메일입니다."}}
        )
    if data.nickname:
        if any(u.get('nickname', '').lower() == data.nickname.lower() for u in active_users):
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
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_deleted": False,
        "deleted_at": None
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
                    user.get("nickname", "").lower() == data.nickname.lower()
                    and user["userId"] != current_user["userId"]
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "status": "error",
                            "data": {"message": "닉네임이 중복되었습니다."}
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



@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(current_user: dict = Depends(get_current_user)):
    users = load_data("users")
    target_user = find_user_by_id(users, current_user["userId"])

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "error","data": {"message": "사용자를 찾을 수 없습니다."}}
        )
    if target_user.get("is_deleted") is True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "data": {"message": "이미 탈퇴한 계정입니다."}}
        )
    soft_delete_user(target_user)
    save_data("users", users)
    return

@router.get("/{userId}")
def get_user(user_id: str):
    #로그인 필요없고 공개 정보만 반환
    users = load_data("users")
    target_user = find_user_by_id(users, user_id)

    #유저가 없거나 탈퇴한 유저면
    if not target_user or target_user.get("is_deleted") is True:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": {"message": "해당 사용자를 찾을 수 없습니다."}
            }
        )
    return {
        "status": "success",
        "data": {
            "userId": target_user["userId"],
            "nickname": target_user["nickname"],
            "profile_image": target_user["profile_image"],
        }
    }