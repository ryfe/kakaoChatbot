# -*- coding: utf-8 -*-
# 단어 JSON 로딩/캐시 + 샘플링 + 개수 파싱

import os, json, random, re
from typing import List, Tuple, Optional
from flask import current_app

# (ko, ja, level) 형식
JLPT_WORDS: List[Tuple[str, str, str]] = []


def load_jlpt_words(path: str) -> List[Tuple[str, str, str]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON을 찾을 수 없습니다: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "JLPT단어" not in data or not isinstance(data["JLPT단어"], list):
        raise ValueError("JSON에 'JLPT단어' 리스트가 없습니다.")
    words = []
    for item in data["JLPT단어"]:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            ko, ja = str(item[0]), str(item[1])
            lv = str(item[2]) if len(item) >= 3 else "JLPT"
            words.append((ko, ja, lv))
    if not words:
        raise ValueError("'JLPT단어'에 유효한 항목이 없습니다.")
    return words


def try_load_into_cache(app=None) -> None:
    global JLPT_WORDS
    app = app or current_app
    path = app.config["JLPT_JSON_PATH"]
    try:
        JLPT_WORDS = load_jlpt_words(path)
        app.logger.info(f"[lexicon] {len(JLPT_WORDS)}개 단어 로드 완료 @ {path}")
    except Exception as e:
        JLPT_WORDS = []
        app.logger.error(f"[lexicon] 로드 실패: {type(e).__name__}: {e}")


def parse_request_count(utterance: str) -> int:
    m = re.search(r"(\d+)", utterance or "")
    return max(1, min(int(m.group(1)) if m else 10, 30))


def pick_random_words(count: int, level: Optional[str] = None) -> List[Tuple[str, str, str]]:
    pool = JLPT_WORDS
    if level:
        pool = [w for w in pool if w[2] == level]
    if not pool:
        return []
    return random.sample(pool, min(count, len(pool)))
