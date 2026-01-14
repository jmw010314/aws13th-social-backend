from pydantic import BaseModel
from datetime import datetime

# 좋아요 상태를 보여줄 때 사용하는 설계도
class LikeStatus(BaseModel):
    is_liked: bool        # 현재 로그인한 유저가 좋아요를 눌렀는지 여부
    total_likes: int      # 이 게시글의 전체 좋아요 수

# (선택) 좋아요 데이터를 저장할 때의 내부 구조
class LikeRecord(BaseModel):
    user_id: str
    post_id: str
    created_at: datetime