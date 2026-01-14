from fastapi import APIRouter, status, HTTPException
from schemas.user import UserCreate, UserLogin, UserUpdate
from datetime import datetime
from utils.auth import get_password_hash
from utils.data import load_data,save_data

router = APIRouter(prefix="/users")

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(data: UserCreate):
    users = load_data("users")


    if any(u.get('email') == data.email for u in users):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"status": "error", "data": {"message": "이미 존재하는 이메일입니다."}}
        )
    if data.nickname:
        if any(u.get('nickname') == data.nickname for u in users):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"status": "error","data":{"message":"닉네임이 중복되었습니다."}}
            )
    new_user = {
        "userId": str(len(users) + 1),
        "email": data.email,
        "name": data.name,
        "password": get_password_hash(data.password),
        "nickname": data.nickname,
        "profile_image": data.profile_image,
        "created_at": datetime.now().isoformat()
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

@router.post("/login")
def login(data: UserLogin):
    return {"message": "로그인 및 토큰 발급"}

@router.get("/me")
def get_me():
    return {"message": "내 프로필 조회"}

@router.patch("/me")
def update_me(data: UserUpdate):
    return {"message": "프로필 수정"}

@router.delete("/me")
def delete_me():
    return {"message": "회원 탈퇴"}

@router.get("/{user_id}")
def get_user(user_id: str):
    return {"message": f"{user_id}번 회원 조회"}