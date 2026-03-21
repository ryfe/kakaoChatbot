# -*- coding: utf-8 -*-
# 카카오 오픈빌더 라우트 + 응답 빌더

import random
from flask import Blueprint, request, jsonify, current_app
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
from . import lexicon
from .lexicon import try_load_into_cache, parse_request_count, pick_random_words
from .examples import build_example_output_from_api

_transliter = Transliter(academic)

bp = Blueprint("kakao", __name__)


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
            for ko, ja in pairs[i:i + 10]
        ]
        outputs.append({"carousel": {"type": "basicCard", "items": items}})
    return outputs


def _simple(text: str) -> dict:
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": text}}]}}


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

        # 단어 생성
        if "단어" in user_msg or "単語" in user_msg:
            count = parse_request_count(user_msg)
            pairs = pick_random_words(count)
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": _word_carousel(pairs),
                    "quickReplies": [
                        {"label": "다시 생성", "action": "message", "messageText": f"한국어 단어 {count}개"},
                        {"label": "5개",    "action": "message", "messageText": "한국어 단어 5개"},
                        {"label": "10개",   "action": "message", "messageText": "한국어 단어 10개"},
                    ]
                }
            }), 200

        # 퀴즈 문제 출제
        if user_msg in ("퀴즈", "다음 문제", "クイズ", "次の問題"):
            pairs = pick_random_words(4)
            correct_ko, correct_ja = pairs[0]
            options = [ko for ko, _ in pairs]
            random.shuffle(options)
            quick_replies = [
                {"label": ko, "action": "message",
                 "messageText": f"퀴즈답 {correct_ja}|{correct_ko}|{ko}"}
                for ko in options
            ]
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": [{"simpleText": {"text": f"「{correct_ja}」의 뜻은?"}}],
                    "quickReplies": quick_replies
                }
            }), 200

        # 퀴즈 정답 처리
        if user_msg.startswith("퀴즈답 "):
            parts = user_msg[4:].strip().split("|")
            if len(parts) == 3:
                ja, correct_ko, chosen_ko = parts
                if chosen_ko == correct_ko:
                    msg = f"✅ 정답!\n「{ja}」= {correct_ko}"
                else:
                    msg = f"❌ 오답\n「{ja}」의 뜻은 {correct_ko}"
                return jsonify({
                    "version": "2.0",
                    "template": {
                        "outputs": [{"simpleText": {"text": msg}}],
                        "quickReplies": [
                            {"label": "다음 문제", "action": "message", "messageText": "퀴즈"},
                            {"label": "단어 보기", "action": "message", "messageText": "한국어 단어 5개"}
                        ]
                    }
                }), 200

        # 기본 에코
        return jsonify(_simple(f"당신이 보낸 메시지: {user_msg}")), 200

    except Exception as e:
        return jsonify(_simple(f"처리 중 오류가 발생했어요: {type(e).__name__}")), 200
