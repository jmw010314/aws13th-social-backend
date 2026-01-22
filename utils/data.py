import json
import os
import logging   #로그 남기기
import shutil
import tempfile   #임시파일 만들기(저장 안정성을 위해)
from typing import Optional, Any, Dict, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
DATA_DIR = "data"

def load_data(filename: str):

    file_path = os.path.join(DATA_DIR, f"{filename}.json")

    # data 폴더가 없으면 생성
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # 파일이 없으면 빈 리스트 저장 후 반환
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []

    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"JSON 파싱 실패: {file_path}. 빈 리스트 반환")
            return []


def save_data(filename: str, data):
    file_path = os.path.join(DATA_DIR, f"{filename}.json")

    # 임시 파일에 먼저 쓰기
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                     delete=False, suffix='.json') as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=4)
        tmp_path = tmp.name

    # 성공 시 원본 교체 (atomic operation)
    shutil.move(tmp_path, file_path)

def ensure_user_fields(user: Dict[str, Any]) -> Dict[str, Any]:
    if "is_deleted" not in user:
        user["is_deleted"] = False
    if "deleted_at" not in user:
        user["deleted_at"] = None
    return user


   #users: 유저 전체 목록(list)
   #userId: 찾고 싶은 유저 id
   #반환: 찾으면 user(dict), 못 찾으면 None

def find_user_by_id(users: List[Dict[str, Any]], userId: str) -> Optional[Dict[str, Any]]:
    for u in users:
        if str(u.get("userId")) == str(userId):
            return ensure_user_fields(u)
    return None

def soft_delete_user(user: Dict[str, Any]) -> Dict[str, Any]:
    # 유저 한명을 완전히 삭제하는게 아니라 탈퇴 처리 상태로만 바꿔준다
    ensure_user_fields(user)
    user["is_deleted"] = True
    user["deleted_at"] = datetime.now(timezone.utc).isoformat()

    if "nickname" in user:
        user["nickname"] = "탈퇴한 사용자"
    if "profile_image" in user:
        user["profile_image"] = None

    return user

# utils/data.py
def get_user_nickname_map(users: list) -> dict:
    return {
        u["userId"]: u.get("nickname")
        for u in users
        if not u.get("is_deleted")
    }