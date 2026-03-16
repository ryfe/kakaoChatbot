# -*- coding: utf-8 -*-
# 환경변수/상수 관리

import os

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 리포 루트

class Config:
    # 통합 단어 JSON 경로(기본: 리포 루트 절대 경로)
    JLPT_JSON_PATH = os.getenv("JLPT_JSON_PATH", os.path.join(_HERE, "words_ja_ko_JLPT.json"))
    # 외부 API 타임아웃(초) — 필요시 조정
    HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "4.0"))
