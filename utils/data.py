import json
import os


DATA_DIR = "data"


def load_data(filename: str):
    """
    JSON 파일을 읽어서 파이썬 리스트/딕셔너리로 반환합니다.
    파일이 없으면 빈 리스트([])를 반환합니다.
    """
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
            return []


def save_data(filename: str, data):
    """
    파이썬 데이터를 JSON 파일로 저장합니다.
    """
    file_path = os.path.join(DATA_DIR, f"{filename}.json")

    with open(file_path, 'w', encoding='utf-8') as f:

        json.dump(data, f, ensure_ascii=False, indent=4)