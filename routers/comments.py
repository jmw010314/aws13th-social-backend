from fastapi import APIRouter, status
from schemas.comment import CommentCreate, CommentUpdate

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.get("/post/{post_id}") # 특정 게시글의 댓글 목록
def get_comments(post_id: str, page: int = 1):
    return {"message": f"{post_id}번 게시글의 {page}페이지 댓글 목록"}

@router.post("/post/{post_id}", status_code=status.HTTP_201_CREATED)
def create_comment(post_id: str, data: CommentCreate):
    return {"message": f"{post_id}번 게시글에 댓글 작성 완료"}

@router.patch("/{comment_id}")
def update_comment(comment_id: str, data: CommentUpdate):
    return {"message": f"{comment_id}번 댓글 수정"}

@router.delete("/{comment_id}")
def delete_comment(comment_id: str):
    return {"message": f"{comment_id}번 댓글 삭제"}

@router.get("/me")
def get_my_comments():
    return {"message": "내가 쓴 댓글 목록 조회"}