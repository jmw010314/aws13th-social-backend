from datetime import datetime
from fastapi import APIRouter, status, Query, Depends, HTTPException
from routers import users
from schemas.post import PostCreate, PostUpdate
from utils.auth import get_current_user
from utils.data import load_data, save_data
from typing import Optional

router = APIRouter(prefix="/posts",tags=["Posts"])

@router.get("")
def get_posts(
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
):
    """
        게시글 목록 조회
        - 공개 API (로그인 불필요)
        - 페이지네이션 적용
        - 목록에서는 제목 + 작성자 닉네임만 반환
    """
    #데이터 로드
    posts = load_data("posts")
    users = load_data("users")

    #삭제되지 않은 게시글만 필터링
    active_posts = [
        p for p in posts if p.get("is_deleted") is not True
    ]
    #페이지네이션 계산
    total = len(active_posts) # 전체 게시글 수
    start = (page - 1) * limit  # 현재 페이지의 시작 인덱스 계산
    end = start + limit  # 현재 페이지의 끝 인덱스 계산
    paged_posts = active_posts[start:end]  # 전체 중 해당 페이지 구간만

    #게시글이 누가 쓴 게시글인지 닉네임으로 알 수 있도록 userId - nickname 매칭
    user_map = {
        u["userId"]: u.get("nickname")
        for u in users
        if u.get("is_deleted") is not True
    }
    data = []
    for post in paged_posts:
        data.append({
            "postId": post["postId"],
            "title": post["title"],
            "nickname": user_map.get(post["userId"], "알 수 없음"), # 여기서 userId는 게시글 작성자
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
@router.post("", status_code=status.HTTP_201_CREATED)
def create_post(
    data: PostCreate,
    current_user: dict = Depends(get_current_user)
):
    # 제목 / 본문 검증
    if not data.title.strip() or not data.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "data": {
                    "message": "제목 또는 본문을 입력해야 합니다."
                }
            }
        )
    # 게시글 데이터 로드
    posts = load_data("posts")
    users = load_data("users")
    #postId 생성
    new_post_Id = (
        max([p["postId"] for p in posts], default=0) + 1
    )
    #현재 시간
    created_at = datetime.now().isoformat()

    #게시글 작성
    new_post = {
        "postId": new_post_Id,
        "userId": current_user["userId"], #작성자 userId
        "title": data.title.strip(),
        "content": data.content.strip(),
        "viewCount": 0,
        "likeCount": 0,
        "created_at": created_at,
        "updated_at": created_at,
        "is_deleted": False,
    }
    posts.append(new_post)  # 게시글 목록에 추가
    save_data("posts", posts)  # 파일에 저장

    #작성자 닉네임 찾기
    user_map = {
        u["userId"]: u.get("nickname")
        for u in users
        if u.get("is_deleted") is not True
    }
    nickname = user_map.get(current_user["userId"], "알 수 없음")

    return {
        "status": "success",
        "data": {
            "title": new_post["title"],
            "content": new_post["content"],
            "nickname": nickname,
            "created_at": created_at,
            "views": 0,
            "likes": 0,
        }
    }


@router.get("/search")
def search_posts(
        keyword: str = Query(..., min_length=1),
):
    """
    게시글 검색
    - 제목 / 내용 / 닉네임 기준 검색
    - 로그인 필요없음
    - 검색 결과 전체 반환
    """
    posts = load_data("posts")
    users = load_data("users")

    user_map = {
        u["userId"]: u.get("nickname")
        for u in users
        if u.get("is_deleted") is not True
    }
    keyword_lower = keyword.lower()
    result = []

    for post in posts:
        # 삭제된 게시글 제외
        if post.get("is_deleted") is True:
            continue
        title = post.get("title", "")
        content = post.get("content", "")
        nickname = user_map.get(post["userId"], "탈퇴한 사용자")

        # 제목 / 내용 / 닉네임 중 하나라도 키워드 포함되면 확인
        if (
            keyword_lower in title.lower()
            or keyword_lower in content.lower()
            or keyword_lower in nickname.lower()
        ):
            result.append({
                "postId": post["postId"],
                "title": title,
                "nickname": nickname,
            })
    return {
        "status": "success",
        "data": result,
    }

@router.get("/me")
def get_my_posts():
    return {"message": "내가 쓴 게시글 목록"}

@router.get("/{postId}")
def get_post(postId: str):
    return {"message": f"{postId}번 상세 조회 (조회수 증가 로직 예정)"}

@router.patch("/{postId}")
def update_post(
    postId: str,
    data: PostUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    게시글 수정
    -로그인 필요
    -본인이 작성한 게시글만 수정 가능
    """
    try:
        postId_int = int(postId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": {
                    "message": "존재하지 않는 게시글입니다."
                }
            }
        )
    posts = load_data("posts")
    post = next(
        (p for p in posts if p["postId"] == postId_int),
        None
    )
    # 게시글이 없거나 삭제된 경우
    if post is None or post.get("is_deleted") is True:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": {
                    "message": "존재하지않는 게시글입니다."
                }
            }
        )
    # 본인이 작성한게 아닌 경우
    if post["userId"] != current_user["userId"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "data": {
                    "message": "게시글을 수정할 권한이 없습니다."
                }
            }
        )
    if data.title is not None:
        if not data.title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "data": {
                        "message": "제목은 비어있을 수 없습니다."
                    }
                }
            )
        post["title"] = data.title.strip()

    if data.content is not None:
        if not data.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "data": {
                        "message": "본문은 비어있을 수 없습니다."
                    }
                }
            )
        post["content"] = data.content.strip()

    #  업데이트 갱신
    post["updated_at"] = datetime.now().isoformat()
    save_data("posts", posts)

    # 작성자 닉네임 찾기
    users = load_data("users")
    user_map = {
        u["userId"]: u.get("nickname")
        for u in users
        if u.get("is_deleted") is not True
    }
    nickname = user_map.get(current_user["userId"], "알 수 없음")

    return {
        "status": "success",
        "data": {
            "postId": postId,  # 받은 그대로 string 반환
            "title": post["title"],
            "content": post["content"],
            "nickname": nickname,
            "createdAt": post["created_at"],
            "updatedAt": post["updated_at"],
            "view": post.get("viewCount", 0),
            "likes": post.get("likeCount", 0),
        }
    }

@router.delete("/{postId}")
def delete_post(postId: str):
    return {"message": f"{postId}번 삭제"}