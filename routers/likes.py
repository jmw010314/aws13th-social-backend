from fastapi import APIRouter, status, Depends, HTTPException
from utils.auth import get_current_user
from utils.data import load_data, save_data
from datetime import datetime, timezone

router = APIRouter(prefix="/likes", tags=["Likes"])


@router.post("/posts/{postId}", status_code=status.HTTP_201_CREATED)
def like_post(
        postId: int,
        current_user: dict = Depends(get_current_user),
):
    """
    게시글에 좋아요 누르기
    - 로그인 필수
    - 중복 좋아요 불가 (이미 눌렀으면 에러)
    """
    # 게시글 존재 확인
    posts = load_data("posts")
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

    # 좋아요 데이터 로드
    likes = load_data("likes")

    # 이미 좋아요 눌렀는지 확인
    existing_like = next(
        (l for l in likes
         if l.get("postId") == postId
         and l.get("userId") == current_user["userId"]
         and not l.get("is_deleted", False)),
        None
    )

    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "error",
                "data": {"message": "이미 좋아요를 눌렀습니다."}
            }
        )

    # 새 좋아요 ID 생성
    new_like_id = max([l.get("likeId", 0) for l in likes], default=0) + 1

    # 좋아요 생성
    new_like = {
        "likeId": new_like_id,
        "postId": postId,
        "userId": current_user["userId"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_deleted": False,
    }

    # 저장
    likes.append(new_like)
    save_data("likes", likes)

    # 게시글의 좋아요 수 증가
    post["likeCount"] = post.get("likeCount", 0) + 1
    save_data("posts", posts)

    # 응답
    return {
        "status": "success",
        "data": {
            "postId": postId,
            "isLiked": True,
            "likeCount": post["likeCount"],
        }
    }



@router.delete("/posts/{postId}", status_code=status.HTTP_204_NO_CONTENT)
def unlike_post(
        postId: int,
        current_user: dict = Depends(get_current_user),
):
    """
    좋아요 취소
    - 로그인 필수
    - 이미 눌렀던 좋아요만 취소 가능
    """
    # 게시글 존재 확인
    posts = load_data("posts")
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

    # 좋아요 데이터 로드
    likes = load_data("likes")

    # 내 좋아요 찾기
    my_like = next(
        (l for l in likes
         if l.get("postId") == postId
         and l.get("userId") == current_user["userId"]
         and not l.get("is_deleted", False)),
        None
    )

    if my_like is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "data": {"message": "좋아요를 누르지 않았습니다."}
            }
        )

    my_like["is_deleted"] = True
    save_data("likes", likes)

    #게시글의 좋아요 수 감소
    post["likeCount"] = max(post.get("likeCount", 1) - 1, 0)
    save_data("posts", posts)

    # 응답 (빈 응답)
    return



@router.get("/posts/{postId}")
def get_like_status(
        postId: int,
        current_user: dict = Depends(get_current_user),
):
    """
    좋아요 상태 확인
    - 로그인 필수
    - 현재 사용자가 좋아요 눌렀는지 + 총 좋아요 수
    """
    # 게시글 존재 확인
    posts = load_data("posts")
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

    # 좋아요 데이터 로드
    likes = load_data("likes")

    # 내가 좋아요 눌렀는지 확인
    my_like = next(
        (l for l in likes
         if l.get("postId") == postId
         and l.get("userId") == current_user["userId"]
         and not l.get("is_deleted", False)),
        None
    )

    # 응답
    return {
        "status": "success",
        "data": {
            "postId": postId,
            "isLiked": my_like is not None,  # True/False
            "likeCount": post.get("likeCount", 0),
        }
    }



@router.get("/me")
def get_my_liked_posts(
        current_user: dict = Depends(get_current_user),
):
    """
    내가 좋아요한 게시글 목록
    - 로그인 필수
    """
    # 데이터 로드
    likes = load_data("likes")
    posts = load_data("posts")
    users = load_data("users")

    # 내가 누른 좋아요 필터링 (취소 안 한 것만)
    my_likes = [
        l for l in likes
        if l.get("userId") == current_user["userId"]
           and not l.get("is_deleted", False)
    ]

    # 좋아요한 게시글 ID 목록
    liked_post_ids = [l["postId"] for l in my_likes]

    # 해당 게시글들 찾기 (삭제 안 된 것만)
    liked_posts = [
        p for p in posts
        if p["postId"] in liked_post_ids
           and not p.get("is_deleted", False)
    ]

    # 최신순 정렬 (좋아요 누른 시간 기준)
    like_time_map = {
        l["postId"]: l["created_at"]
        for l in my_likes
    }

    liked_posts.sort(
        key=lambda p: like_time_map.get(p["postId"], ""),
        reverse=True
    )

    # 작성자 닉네임 매핑
    from utils.data import get_user_nickname_map
    user_map = get_user_nickname_map(users)

    # 응답 데이터 생성
    data = [
        {
            "postId": p["postId"],
            "title": p["title"],
            "nickname": user_map.get(p["userId"], "알 수 없음"),
            "likeCount": p.get("likeCount", 0),
            "viewCount": p.get("viewCount", 0),
            "created_at": p["created_at"],
        }
        for p in liked_posts
    ]

    return {
        "status": "success",
        "data": data,
    }