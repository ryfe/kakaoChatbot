# -*- coding: utf-8 -*-
# 카카오 오픈빌더 웹훅 라우트

import re
from flask import Blueprint, request, jsonify, current_app
from .. import lexicon
from ..lexicon import try_load_into_cache, parse_request_count, pick_random_words
from ..examples import fetch_example
from ..db import save_quiz_result, get_user_stats
from ..core.vocab import parse_level
from ..core.quiz import generate_quiz, check_answer, format_stats
from . import builder as build

bp = Blueprint("kakao", __name__)


def _user(body: dict) -> tuple[str, str]:
    """(user_msg, user_id) 추출"""
    ur = body.get("userRequest") or {}
    msg = (ur.get("utterance") or "").strip()
    uid = (ur.get("user") or {}).get("id", "unknown")
    return msg, uid


@bp.route("/health", methods=["GET"])
def health():
    return "OK", 200


@bp.route("/reload", methods=["POST"])
def reload_lexicon():
    try_load_into_cache()
    msg = (
        f"로드 {'성공' if lexicon.JLPT_WORDS else '실패'} — "
        f"현재 {len(lexicon.JLPT_WORDS)}개 단어 @ {current_app.config['JLPT_JSON_PATH']}"
    )
    return jsonify(build.simple(msg)), 200


@bp.route("/kakao", methods=["POST"])
def kakao_webhook():
    try:
        body    = request.get_json(silent=True) or {}
        msg, uid = _user(body)

        # 발음
        if msg.startswith("발음 "):
            rest = msg[3:].strip()
            ko, ja = (s.strip() for s in rest.split("|", 1)) if "|" in rest else (rest, rest)
            return jsonify(build.pronunciation(ko, ja)), 200

        # 예문
        if msg.startswith("예문 "):
            rest = msg[3:].strip()
            ko, ja = (s.strip() for s in rest.split("|", 1)) if "|" in rest else (rest, rest)
            example = fetch_example(ja)
            return jsonify(build.example_card(ko, ja, example)), 200

        # 단어 데이터 미로드
        if not lexicon.JLPT_WORDS:
            return jsonify(build.simple(
                f"단어 데이터가 로드되지 않았습니다.\n"
                f"JSON 경로: {current_app.config['JLPT_JSON_PATH']}\n"
                "관리자: /reload 로 재로드 가능"
            )), 200

        # 단어 생성
        if "단어" in msg or "単語" in msg:
            count = parse_request_count(msg)
            level = parse_level(msg)
            pairs = pick_random_words(count, level)
            return jsonify(build.word_carousel(pairs, level, count)), 200

        # 퀴즈 문제
        if msg in ("퀴즈", "다음 문제", "クイズ", "次の問題") \
                or re.match(r"^(초급|중급|고급) 퀴즈$", msg):
            level = parse_level(msg)
            quiz  = generate_quiz(level)
            if not quiz:
                return jsonify(build.simple("단어 데이터가 없습니다.")), 200
            return jsonify(build.quiz_question(quiz)), 200

        # 내 점수
        if msg in ("내 점수", "점수", "スコア"):
            stats = get_user_stats(uid)
            return jsonify(build.simple(format_stats(stats))), 200

        # 퀴즈 정답 처리
        if msg.startswith("퀴즈답 "):
            parts = msg[4:].strip().split("|")
            if len(parts) == 3:
                ko, correct_ja, chosen_ja = parts
                is_correct = check_answer(correct_ja, chosen_ja)
                save_quiz_result(uid, is_correct, ko, correct_ja, "")
                return jsonify(build.quiz_result(is_correct, ko, correct_ja)), 200

        # 기본 에코
        return jsonify(build.simple(f"당신이 보낸 메시지: {msg}")), 200

    except Exception as e:
        return jsonify(build.simple(f"처리 중 오류가 발생했어요: {type(e).__name__}")), 200
