# -*- coding: utf-8 -*-
# LINE Messaging API 웹훅 라우트

import re, hmac, hashlib, base64
import requests as _req
from flask import Blueprint, request, jsonify, current_app
from .. import lexicon
from ..lexicon import parse_request_count, pick_random_words
from ..examples import fetch_example
from ..db import save_quiz_result, get_user_stats
from ..core.vocab import parse_level
from ..core.quiz import generate_quiz, check_answer, format_stats
from . import builder as build

bp = Blueprint("line", __name__)

_LINE_REPLY = "https://api.line.me/v2/bot/message/reply"


def _verify(body_bytes: bytes, signature: str, secret: str) -> bool:
    """LINE 서명 검증"""
    digest = hmac.new(secret.encode(), body_bytes, hashlib.sha256).digest()
    return base64.b64encode(digest).decode() == signature


def _reply(reply_token: str, messages: list) -> None:
    """LINE reply API 호출"""
    token = current_app.config.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    if not token:
        current_app.logger.warning("[line] LINE_CHANNEL_ACCESS_TOKEN 미설정")
        return
    _req.post(
        _LINE_REPLY,
        headers={"Authorization": f"Bearer {token}"},
        json={"replyToken": reply_token, "messages": messages},
        timeout=5,
    )


@bp.route("/line", methods=["POST"])
def line_webhook():
    # ── 서명 검증 ────────────────────────────────────────────
    secret = current_app.config.get("LINE_CHANNEL_SECRET", "")
    if secret:
        sig = request.headers.get("X-Line-Signature", "")
        if not _verify(request.data, sig, secret):
            return "Forbidden", 403

    body = request.get_json(silent=True) or {}

    for event in body.get("events", []):
        if event.get("type") != "message":
            continue
        if (event.get("message") or {}).get("type") != "text":
            continue

        reply_token = event.get("replyToken", "")
        msg = (event["message"].get("text") or "").strip()
        uid = (event.get("source") or {}).get("userId", "unknown")

        messages = _handle(msg, uid)
        if messages:
            _reply(reply_token, messages)

    return jsonify({"status": "ok"}), 200


def _handle(msg: str, uid: str) -> list[dict]:
    """메시지 처리 → LINE messages 리스트"""
    # 발음
    if msg.startswith("발음 "):
        rest = msg[3:].strip()
        ko, ja = (s.strip() for s in rest.split("|", 1)) if "|" in rest else (rest, rest)
        return [build.pronunciation(ko, ja)]

    # 예문
    if msg.startswith("예문 "):
        rest = msg[3:].strip()
        ko, ja = (s.strip() for s in rest.split("|", 1)) if "|" in rest else (rest, rest)
        return build.example_card(ko, ja, fetch_example(ja))

    # 단어 데이터 미로드
    if not lexicon.JLPT_WORDS:
        return [build.text("단어 데이터가 로드되지 않았습니다.")]

    # 단어 생성
    if "단어" in msg or "単語" in msg:
        count = parse_request_count(msg)
        level = parse_level(msg)
        pairs = pick_random_words(count, level)
        return build.word_list(pairs, level, count)

    # 퀴즈 문제
    if msg in ("퀴즈", "다음 문제", "クイズ", "次の問題") \
            or re.match(r"^(초급|중급|고급) 퀴즈$", msg):
        level = parse_level(msg)
        quiz  = generate_quiz(level)
        if not quiz:
            return [build.text("단어 데이터가 없습니다.")]
        return build.quiz_question(quiz)

    # 내 점수
    if msg in ("내 점수", "점수", "スコア"):
        stats = get_user_stats(uid)
        return [build.text(format_stats(stats))]

    # 퀴즈 정답 처리
    if msg.startswith("퀴즈답 "):
        parts = msg[4:].strip().split("|")
        if len(parts) == 3:
            ko, correct_ja, chosen_ja = parts
            is_correct = check_answer(correct_ja, chosen_ja)
            save_quiz_result(uid, is_correct, ko, correct_ja, "")
            return build.quiz_result(is_correct, ko, correct_ja)

    # 기본 에코
    return [build.text(f"당신이 보낸 메시지: {msg}")]
