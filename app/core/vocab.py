# -*- coding: utf-8 -*-
# 단어 / 발음 관련 공통 로직

from hangul_romanize import Transliter
from hangul_romanize.rule import academic

_transliter = Transliter(academic)

LEVEL_MAP = {
    "초급": "초급", "쉬운": "초급", "beginner": "초급",
    "중급": "중급", "보통": "중급", "intermediate": "중급",
    "고급": "고급", "어려운": "고급", "advanced": "고급",
}


def romanize(ko: str) -> str:
    """한국어 → 로마자 발음"""
    return _transliter.translit(ko)


def parse_level(msg: str) -> str | None:
    """메시지에서 레벨 키워드 추출"""
    for key, lv in LEVEL_MAP.items():
        if key in msg:
            return lv
    return None
