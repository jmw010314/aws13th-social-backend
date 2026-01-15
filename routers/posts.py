from fastapi import APIRouter, status, Query
from schemas.post import PostCreate, PostUpdate
from typing import Optional

router = APIRouter(prefix="/posts",tags=["Posts"])

@router.get("") # 목록 조회, 검색, 정렬 포함
def get_posts(page: int = 1, search: Optional[str] = None, sort: str = "latest"):
    return {"message": f"{page}페이지 {sort}순 목록 조회 (검색어: {search})"}

@router.post("", status_code=status.HTTP_201_CREATED)
def create_post(data: PostCreate):
    return {"message": "게시글 작성"}

@router.get("/me")
def get_my_posts():
    return {"message": "내가 쓴 게시글 목록"}

@router.get("/{post_id}")
def get_post(post_id: str):
    return {"message": f"{post_id}번 상세 조회 (조회수 증가 로직 예정)"}

@router.patch("/{post_id}")
def update_post(post_id: str, data: PostUpdate):
    return {"message": f"{post_id}번 수정"}

@router.delete("/{post_id}")
def delete_post(post_id: str):
    return {"message": f"{post_id}번 삭제"}