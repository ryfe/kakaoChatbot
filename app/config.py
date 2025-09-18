# -*- coding: utf-8 -*-
# 환경변수/상수 관리

import os

class Config:
    # 통합 단어 JSON 경로(기본: 리포 루트)
    JLPT_JSON_PATH = os.getenv("JLPT_JSON_PATH", "./words_ja_ko_JLPT.json")
    # 외부 API 타임아웃(초) — 필요시 조정
    HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "4.0"))
