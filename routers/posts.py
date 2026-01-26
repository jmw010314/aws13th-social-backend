from enum import Enum
from fastapi import APIRouter, status, Query, Depends, HTTPException
from schemas.post import PostCreate, PostUpdate
from utils.auth import get_current_user
from utils.data import load_data, save_data, get_user_nickname_map
from datetime import datetime, timezone

router = APIRouter(prefix="/posts", tags=["Posts"])

#Enum 클래스 추가
class SortOption(str, Enum):
    LATEST = "latest"
    VIEWS = "views"
    LIKES = "likes"

@router.get("")
def get_posts(
        page: int = Query(1, ge=1),  # 기본값 1페이지, 1보다 커야됌
        limit: int = Query(20, ge=1, le=100),  # 한 페이지당 20개, 최대 100개
        sort: SortOption = Query(SortOption.LATEST),
):
    """
        게시글 목록 조회
        - 공개 API (로그인 불필요)
        - 페이지네이션 적용
        - 목록에서는 제목 + 작성자 닉네임만 반환
    """
    # 데이터 로드
    posts = load_data("posts")  # 데이터베이스 대신 json 로드
    users = load_data("users")

    # 삭제되지 않은 게시글만 필터링
    active_posts = [
        p for p in posts if not p.get("is_deleted", False)
    ]
    # 정렬 추가
    if sort == SortOption.LATEST:
        active_posts.sort(
            key=lambda p: p.get("created_at", ""),
            reverse=True
        )
    elif sort == SortOption.VIEWS:
        active_posts.sort(
            key=lambda p: p.get("viewCount", 0),
            reverse=True
        )

    elif sort == SortOption.LIKES:
        active_posts.sort(
            key=lambda p: p.get("likeCount", 0),
            reverse=True
        )
    # 페이지네이션 계산
    total = len(active_posts)  # 전체 게시글 수
    start = (page - 1) * limit  # 현재 페이지의 시작 인덱스 계산
    end = start + limit  # 현재 페이지의 끝 인덱스 계산
    paged_posts = active_posts[start:end]  # 전체 중 해당 페이지 구간만

    # 게시글이 누가 쓴 게시글인지 닉네임으로 알 수 있도록 userId - nickname 매칭
    user_map = get_user_nickname_map(users)

    data = []
    for post in paged_posts:
        data.append({
            "postId": post["postId"],
            "title": post["title"],
            "nickname": user_map.get(post["userId"], "알 수 없음"),  # 여기서 userId는 게시글 작성자
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
        # 새 게시글 작성 (로그인 필수)
        data: PostCreate,
        current_user: dict = Depends(get_current_user)
):
    # 제목 / 본문 검증
    if not data.title.strip() or not data.content.strip():  # strip()으로 양끝 공백 제거
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
    # postId 생성
    new_post_id = (  # 마지막 게시글 ID에 1 추가해 고우 ID 생성
            max([p.get("postId", 0)  for p in posts], default=0) + 1
    )
    # 현재 시간
    created_at = datetime.now(timezone.utc).isoformat()

    # 게시글 작성
    new_post = {
        "postId": new_post_id,
        "userId": current_user["userId"],  # 작성자 userId
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

    # 작성자 닉네임(current_user에 이미 있음)
    nickname = current_user.get("nickname", "알 수 없음")
    return {
        "status": "success",
        "data": {
            "title": new_post["title"],
            "content": new_post["content"],
            "nickname": nickname,
            "created_at": created_at,
            "viewCount": 0,
            "likeCount": 0,
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

    user_map = get_user_nickname_map(users)

    keyword_lower = keyword.lower()
    result = []

    for post in posts:
        # 삭제된 게시글 제외
        if post.get("is_deleted") is True:
            continue
        title = post.get("title", "")
        content = post.get("content", "")
        nickname = user_map.get(post.get("userId"), "알 수 없음")

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
def get_my_posts(
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        sort: SortOption = Query(SortOption.LATEST),
        current_user: dict = Depends(get_current_user),
):
    posts = load_data("posts")

    # 내가 쓴 게시글  + 삭제 안된 게시글만
    my_posts = [
        p for p in posts
        if p["userId"] == current_user["userId"]
           and not p.get("is_deleted", False)
    ]

    # 정렬
    if sort == SortOption.LATEST:
        my_posts.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    elif sort == SortOption.VIEWS:
        my_posts.sort(key=lambda p: p.get("viewCount", 0), reverse=True)
    elif sort == SortOption.LIKES:
        my_posts.sort(key=lambda p: p.get("likeCount", 0), reverse=True)

    # 페이지네이션
    total = len(my_posts)
    start = (page - 1) * limit
    end = start + limit
    paged_posts = my_posts[start:end]

    data = [
        {
            "postId": p["postId"],
            "title": p["title"],
            "created_at": p["created_at"],
            "viewCount": p.get("viewCount", 0),
            "likeCount": p.get("likeCount", 0),
        }
        for p in paged_posts
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


@router.get("/{postId}")
def get_post(
        postId: int,
        _current_user: dict = Depends(get_current_user),
):
    """
    게시글 상세 조회
    - 조회 시마다 조회수 1 증가
    - 삭제된 게시글은 조회 불가
    """
    # 데이터 로드

    posts = load_data("posts")
    users = load_data("users")

    # 해당 postId를 가진 게시글 찾기
    post = next(
        (p for p in posts if p["postId"] == postId),
        None
    )

    # 게시글이 없거나 삭제된 경우 체크
    if post is None or post.get("is_deleted") is True:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": {
                    "message": "존재하지 않는 게시글입니다."
                }
            }
        )
    # 조회수 증가 및 저장
    post["viewCount"] = post.get("viewCount", 0) + 1
    save_data("posts", posts)

    # 작성자 닉네임 찾기
    user_map = get_user_nickname_map(users)
    nickname = user_map.get(post["userId"], "알 수 없음")

    # 응답
    return {
        "status": "success",
        "data": {
            "postId": post["postId"],
            "title": post["title"],
            "content": post["content"],
            "nickname": nickname,
            "created_at": post.get("created_at"),
            "updated_at": post.get("updated_at"),
            "viewCount": post["viewCount"],
            "likeCount": post.get("likeCount", 0)
        }
    }


@router.patch("/{postId}")
def update_post(
        postId: int,
        data: PostUpdate,
        current_user: dict = Depends(get_current_user),
):
    """
    게시글 수정
    -로그인 필요
    -본인이 작성한 게시글만 수정 가능
    """
    posts = load_data("posts")

    post = next(
        (p for p in posts if p["postId"] == postId),
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
    post["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_data("posts", posts)

    # 작성자 닉네임 찾기
    nickname = current_user.get("nickname", "알 수 없음")

    return {
        "status": "success",
        "data": {
            "postId": post["postId"],
            "title": post["title"],
            "content": post["content"],
            "nickname": nickname,
            "created_at": post["created_at"],
            "updated_at": post["updated_at"],
            "viewCount": post.get("viewCount", 0),
            "likeCount": post.get("likeCount", 0),
        }
    }


@router.delete("/{postId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
        postId: int,
        current_user: dict = Depends(get_current_user),
):
    posts = load_data("posts")
    post = next(
        (p for p in posts if p["postId"] == postId),
        None
    )

    # 게시글이 없거나 이미 삭제된 경우
    if post is None or post.get("is_deleted", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": {"message": "존재하지 않는 게시글입니다."}
            }
        )
    # 게시글이 본인 글인지
    if post["userId"] != current_user["userId"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "error",
                "data": {"message": "게시글을 삭제할 권한이 없습니다."}
            }
        )
    post["is_deleted"] = True
    post["updated_at"] = datetime.now(timezone.utc).isoformat()

    save_data("posts", posts)
    return