# -*- coding: utf-8 -*-
# 퀴즈 / 점수 관련 공통 로직

import random
from typing import Optional
from ..lexicon import pick_random_words


def generate_quiz(level: Optional[str] = None) -> dict | None:
    """
    퀴즈 문제 데이터 반환.
    Returns: {ko, correct_ja, options: [str, str, str, str]} or None
    """
    pairs = pick_random_words(4, level)
    if not pairs:
        return None
    correct_ko, correct_ja, *_ = pairs[0]
    options = [p[1] for p in pairs]
    random.shuffle(options)
    return {"ko": correct_ko, "correct_ja": correct_ja, "options": options}


def check_answer(correct_ja: str, chosen_ja: str) -> bool:
    return correct_ja == chosen_ja


def format_stats(stats: dict) -> str:
    """점수 dict → 표시 텍스트"""
    if not stats or stats.get("total", 0) == 0:
        return "아직 퀴즈 기록이 없습니다.\n「퀴즈」로 시작해보세요!"
    rate = int(stats["correct"] / stats["total"] * 100)
    return (
        f"📊 퀴즈 점수\n"
        f"정답: {stats['correct']} / {stats['total']}문제\n"
        f"정답률: {rate}%"
    )
