import json
import os
import logging
import shutil
import tempfile

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