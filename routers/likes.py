from fastapi import APIRouter, status
from schemas.likes import LikeStatus # 스키마 불러오기

router = APIRouter(prefix="/likes", tags=["Likes"])

# 특정 게시글의 좋아요 상태 확인 (스키마 적용)
@router.get("/post/{post_id}/status", response_model=LikeStatus)
def get_like_status(post_id: str):
    # 나중에 여기서 실제 DB(JSON)를 조회해서 데이터를 가져오게 됩니다.
    return {
        "is_liked": True,
        "total_likes": 42
    }

@router.post("/post/{post_id}", status_code=status.HTTP_201_CREATED)
def add_like(post_id: str):
    return {"status": "success", "message": f"{post_id}번 게시글 좋아요 완료"}

@router.delete("/post/{post_id}")
def remove_like(post_id: str):
    return {"status": "success", "message": f"{post_id}번 게시글 좋아요 취소"}