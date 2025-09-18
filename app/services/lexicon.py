# -*- coding: utf-8 -*-
# 단어 JSON 로딩/캐시 + 샘플링 + 개수 파싱

import os, json, random, re
from typing import List, Tuple
from flask import current_app

# 메모리 캐시: [("한국어","일본어"), ...]
JLPT_WORDS: List[Tuple[str, str]] = []

def load_jlpt_words(path: str) -> List[Tuple[str, str]]:
    """
    JSON 파일을 읽어 [("한국어","일본어"), ...] 형태로 변환.
    JSON 예시:
    {
      "JLPT단어": [
        ["만나다", "会う"],
        ["파랗다", "青い"]
      ]
    }
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"통합 JSON을 찾을 수 없습니다: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "JLPT단어" not in data or not isinstance(data["JLPT단어"], list):
        raise ValueError("JSON에 'JLPT단어' 리스트가 없습니다.")
    words: List[Tuple[str, str]] = []
    for item in data["JLPT단어"]:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            ko, ja = str(item[0]), str(item[1])
            words.append((ko, ja))
    if not words:
        raise ValueError("'JLPT단어'에 유효한 항목이 없습니다.")
    return words

def try_load_into_cache(app=None) -> None:
    """
    서버 시작 시/리로드 시 캐시에 단어 데이터 적재.
    """
    global JLPT_WORDS
    app = app or current_app
    path = app.config["JLPT_JSON_PATH"]
    try:
        JLPT_WORDS = load_jlpt_words(path)
        app.logger.info(f"[lexicon] 단어 로드 완료: {len(JLPT_WORDS)}개 @ {path}")
    except Exception as e:
        JLPT_WORDS = []
        app.logger.error(f"[lexicon] 단어 로드 실패: {type(e).__name__}: {e}")

def parse_request_count(utterance: str) -> int:
    """
    발화에서 숫자 추출 → 개수로 사용. 없으면 기본 10개.
    캐러셀/출력 제약 고려해 상한은 30으로 설정(안전선).
    """
    text = (utterance or "").strip()
    m = re.search(r"(\d+)", text)
    count = int(m.group(1)) if m else 10
    return max(1, min(count, 30))

def pick_random_words(count: int) -> List[Tuple[str, str]]:
    """
    캐시된 JLPT_WORDS에서 랜덤 샘플링.
    """
    if not JLPT_WORDS:
        return []
    if count >= len(JLPT_WORDS):
        tmp = JLPT_WORDS[:]
        random.shuffle(tmp)
        return tmp[:count]
    return random.sample(JLPT_WORDS, count)
