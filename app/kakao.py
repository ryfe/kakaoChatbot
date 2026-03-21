# -*- coding: utf-8 -*-
# 카카오 오픈빌더 라우트 + 응답 빌더

import random, re
from flask import Blueprint, request, jsonify, current_app
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
from . import lexicon
from .lexicon import try_load_into_cache, parse_request_count, pick_random_words
from .examples import build_example_output_from_api
from .db import save_quiz_result, get_user_stats

_transliter = Transliter(academic)

bp = Blueprint("kakao", __name__)

LEVEL_MAP = {
    "초급": "초급", "쉬운": "초급", "beginner": "초급",
    "중급": "중급", "보통": "중급", "intermediate": "중급",
    "고급": "고급", "어려운": "고급", "advanced": "고급",
}


# ── 응답 빌더 ────────────────────────────────────────────────

def _pronunciation(ko: str, ja: str) -> dict:
    roman = _transliter.translit(ko)
    return _simple(f"{ko}\n[{roman}]\n{ja}")


def _word_carousel(pairs: list) -> list:
    """단어 쌍 → 캐러셀 outputs (10장 단위 분할)"""
    outputs = []
    for i in range(0, len(pairs), 10):
        items = [
            {
                "title": f"{ko} [{_transliter.translit(ko)}]",
                "description": ja,
                "buttons": [
                    {"action": "message", "label": "📝 예문 보기", "messageText": f"예문 {ko}|{ja}"}
                ]
            }
            for ko, ja, *_ in pairs[i:i + 10]
        ]
        outputs.append({"carousel": {"type": "basicCard", "items": items}})
    return outputs


def _simple(text: str) -> dict:
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": text}}]}}


def _parse_level(msg: str):
    """메시지에서 레벨 키워드 추출 → (level or None, 원본 메시지)"""
    for key, lv in LEVEL_MAP.items():
        if key in msg:
            return lv
    return None


# ── 라우트 ───────────────────────────────────────────────────

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
    return jsonify(_simple(msg)), 200


@bp.route("/kakao", methods=["POST"])
def kakao_webhook():
    try:
        body = request.get_json(silent=True) or {}
        user_msg = ((body.get("userRequest") or {}).get("utterance") or "").strip()
        user_id  = ((body.get("userRequest") or {}).get("user") or {}).get("id", "unknown")

        # 발음
        if user_msg.startswith("발음 "):
            rest = user_msg[3:].strip()
            ko, ja = (s.strip() for s in rest.split("|", 1)) if "|" in rest else (rest, rest)
            return jsonify(_pronunciation(ko, ja)), 200

        # 예문
        if user_msg.startswith("예문 "):
            rest = user_msg[3:].strip()
            ko, ja = (s.strip() for s in rest.split("|", 1)) if "|" in rest else (rest, rest)
            return jsonify(build_example_output_from_api(ko, ja)), 200

        # 단어 없음 안내
        if not lexicon.JLPT_WORDS:
            return jsonify(_simple(
                "단어 데이터가 로드되지 않았습니다.\n"
                f"JSON 경로: {current_app.config['JLPT_JSON_PATH']}\n"
                "관리자: /reload 로 재로드 가능"
            )), 200

        # 단어 생성 (레벨 포함/미포함)
        if "단어" in user_msg or "単語" in user_msg:
            count = parse_request_count(user_msg)
            level = _parse_level(user_msg)
            pairs = pick_random_words(count, level)
            level_label = f"{level} " if level else ""
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": _word_carousel(pairs),
                    "quickReplies": [
                        {"label": "다시 생성", "action": "message", "messageText": f"{level_label}단어 {count}개"},
                        {"label": "초급",     "action": "message", "messageText": f"초급 단어 {count}개"},
                        {"label": "중급",     "action": "message", "messageText": f"중급 단어 {count}개"},
                        {"label": "고급",     "action": "message", "messageText": f"고급 단어 {count}개"},
                    ]
                }
            }), 200

        # 퀴즈 문제 출제
        if user_msg in ("퀴즈", "다음 문제", "クイズ", "次の問題") or re.match(r"^(초급|중급|고급) 퀴즈$", user_msg):
            level = _parse_level(user_msg)
            pairs = pick_random_words(4, level)
            correct_ko, correct_ja, *_ = pairs[0]
            options = [p[1] for p in pairs]
            random.shuffle(options)
            quick_replies = [
                {"label": ja, "action": "message",
                 "messageText": f"퀴즈답 {correct_ko}|{correct_ja}|{ja}"}
                for ja in options
            ]
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": [{"simpleText": {"text": f"「{correct_ko}」의 일본어는?"}}],
                    "quickReplies": quick_replies
                }
            }), 200

        # 내 점수
        if user_msg in ("내 점수", "점수", "スコア"):
            stats = get_user_stats(user_id)
            if not stats or stats["total"] == 0:
                msg = "아직 퀴즈 기록이 없습니다.\n「퀴즈」로 시작해보세요!"
            else:
                rate = int(stats["correct"] / stats["total"] * 100)
                msg = f"📊 퀴즈 점수\n정답: {stats['correct']} / {stats['total']}문제\n정답률: {rate}%"
            return jsonify(_simple(msg)), 200

        # 퀴즈 정답 처리
        if user_msg.startswith("퀴즈답 "):
            parts = user_msg[4:].strip().split("|")
            if len(parts) == 3:
                ko, correct_ja, chosen_ja = parts
                is_correct = chosen_ja == correct_ja
                save_quiz_result(user_id, is_correct, ko, correct_ja, "")
                if is_correct:
                    msg = f"✅ 정답!\n「{ko}」= {correct_ja}"
                else:
                    msg = f"❌ 오답\n「{ko}」의 일본어는 {correct_ja}"
                return jsonify({
                    "version": "2.0",
                    "template": {
                        "outputs": [{"simpleText": {"text": msg}}],
                        "quickReplies": [
                            {"label": "다음 문제", "action": "message", "messageText": "퀴즈"},
                            {"label": "점수", "action": "message", "messageText": "내 점수"},
                            {"label": "단어 보기", "action": "message", "messageText": "한국어 단어 5개"}
                        ]
                    }
                }), 200

        # 기본 에코
        return jsonify(_simple(f"당신이 보낸 메시지: {user_msg}")), 200

    except Exception as e:
        return jsonify(_simple(f"처리 중 오류가 발생했어요: {type(e).__name__}")), 200
