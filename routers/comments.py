from operator import length_hint

from fastapi import APIRouter, status, Query, Depends, HTTPException
from schemas.comment import CommentCreate, CommentUpdate
from utils.auth import get_current_user
from utils.data import load_data, save_data, get_user_nickname_map
from datetime import datetime, timezone
router = APIRouter(prefix="/comments", tags=["Comments"])

@router.get("/post/{postId}") # 특정 게시글의 댓글 목록
def get_comments(
    postId: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    #데이터 로드
    comments = load_data("comments")
    users = load_data("users")
    posts = load_data("posts")

    # 게시글 존재확인
    post = next(
        (p for p in posts if p["postId"] == postId),
        None
    )
    if post is None or post.get("is_deleted"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": {"message": "존재하지 않는 게시글입니다."}
            }
        )
    # 해당 게시글의 댓글 필터일(삭제 안된것만)
    post_comments = [
        c for c in comments
        if c.get("postId") == postId
        and not c.get("is_deleted",False)
    ]

    #최신순 정렬
    post_comments.sort(
        key=lambda c: c.get("created_at", ""),
        reverse=True
    )

    # 페이지네이션
    total = len(post_comments)
    start = (page - 1) * limit
    end = start + limit
    paged_comments = post_comments[start:end]

    # 작성자 닉네임 매핑
    user_map = get_user_nickname_map(users)

    # 응답
    data = [
        {
            "commentId": c["commentId"],
            "content": c["content"],
            "nickname": user_map.get(c["userId"], "알 수 없음"),
            "created_at": c["created_at"],
            "updated_at": c.get("updated_at"),
        }
        for c in paged_comments
    ]
    return {
        "status": "success",
        "data": data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
        }
    }

@router.post("/post/{postId}", status_code=status.HTTP_201_CREATED)
def create_comment(
    postId: int,
    data: CommentCreate,
    current_user: dict = Depends(get_current_user),
):
    #내용 검증
    if not data.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "data": {"message": "댓글 내용을 입력해야 합니다."}
            }
        )
    # 존재 확인
    posts = load_data("posts")
    post = next(
        (p for p in posts if p.get("postId") == postId),
        None
    )

    if post is None or post.get("is_deleted"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": {"message": "존재하지 않는 게시글입니다."}
            }
        )
    comments = load_data("comments")
    new_comment_id = max([c.get("commentId", 0) for c in comments], default=0) + 1

    created_at = datetime.now(timezone.utc).isoformat()

    new_comment = {
        "commentId": new_comment_id,
        "postId": postId,  # 어느 게시글의 댓글인지
        "userId": current_user["userId"],  # 댓글 작성자
        "content": data.content.strip(),
        "created_at": created_at,
        "updated_at": created_at,
        "is_deleted": False,
    }
    comments.append(new_comment)
    save_data("comments", comments)

    # ⑧ 응답
    return {
        "status": "success",
        "data": {
            "commentId": new_comment_id,
            "postId": postId,
            "content": new_comment["content"],
            "nickname": current_user.get("nickname", "알 수 없음"),
            "created_at": created_at,
        }
    }

@router.patch("/{commentId}")
def update_comment(
        commentId: int,
        data: CommentUpdate,
        current_user: dict = Depends(get_current_user),
):
    """
    댓글 수정
    - 로그인 필수
    - 본인 댓글만 수정 가능
    """
    # 댓글 불러오기
    comments = load_data("comments")

    # 댓글 찾기
    comment = next(
        (c for c in comments if c["commentId"] == commentId),
        None
    )

    # 댓글 존재 확인
    if comment is None or comment.get("is_deleted"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": {"message": "존재하지 않는 댓글입니다."}
            }
        )

    # 권한 확인 (본인 댓글인지)
    if comment["userId"] != current_user["userId"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "data": {"message": "댓글을 수정할 권한이 없습니다."}
            }
        )

    # 내용 수정
    if data.content is not None:
        if not data.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "data": {"message": "댓글 내용은 비어있을 수 없습니다."}
                }
            )
        comment["content"] = data.content.strip()

    # 수정 시간 업데이트
    comment["updated_at"] = datetime.now(timezone.utc).isoformat()

    # 저장
    save_data("comments", comments)

    # 응답
    return {
        "status": "success",
        "data": {
            "commentId": comment["commentId"],
            "content": comment["content"],
            "created_at": comment["created_at"],
            "updated_at": comment["updated_at"],
        }
    }
@router.delete("/{commentId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
        commentId: int,
        current_user: dict = Depends(get_current_user),
):
    """
    댓글 삭제
    - 로그인 필수
    - 본인 댓글만 삭제 가능
    """
    # 댓글 불러오기
    comments = load_data("comments")

    # 댓글 찾기
    comment = next(
        (c for c in comments if c["commentId"] == commentId),
        None
    )

    #  댓글 존재 확인
    if comment is None or comment.get("is_deleted"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": {"message": "존재하지 않는 댓글입니다."}
            }
        )

    # 권한 확인 (본인 댓글인지)
    if comment["userId"] != current_user["userId"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "data": {"message": "댓글을 삭제할 권한이 없습니다."}
            }
        )

    comment["is_deleted"] = True
    comment["updated_at"] = datetime.now(timezone.utc).isoformat()

    # 저장
    save_data("comments", comments)

    # 응답
    return
@router.get("/me")
def get_my_comments(
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
):
    """
    내가 쓴 댓글 목록
    - 로그인 필수
    """
    # 데이터 로드
    comments = load_data("comments")
    posts = load_data("posts")

    # 내가 쓴 댓글만 필터링 (삭제 안 된 것만)
    my_comments = [
        c for c in comments
        if c["userId"] == current_user["userId"]
           and not c.get("is_deleted", False)
    ]

    # 최신순 정렬
    my_comments.sort(
        key=lambda c: c.get("created_at", ""),
        reverse=True
    )

    # 페이지네이션
    total = len(my_comments)
    start = (page - 1) * limit
    end = start + limit
    paged_comments = my_comments[start:end]

    # 게시글 정보 포함해서 응답 데이터 생성
    data = []
    for c in paged_comments:
        # 댓글이 달린 게시글 찾기
        post = next(
            (p for p in posts if p["postId"] == c["postId"]),
            None
        )

        data.append({
            "commentId": c["commentId"],
            "postId": c["postId"],
            "postTitle": post["title"] if post else "삭제된 게시글",
            "content": c["content"],
            "created_at": c["created_at"],
        })

    return {
        "status": "success",
        "data": data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
        }
    }
