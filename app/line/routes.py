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
from ..core.quiz import generate_quiz, check_answer
from . import builder as build

bp = Blueprint("line", __name__)

_LINE_REPLY = "https://api.line.me/v2/bot/message/reply"


def _verify(body_bytes: bytes, signature: str, secret: str) -> bool:
    digest = hmac.new(secret.encode(), body_bytes, hashlib.sha256).digest()
    return base64.b64encode(digest).decode() == signature


def _reply(reply_token: str, messages: list) -> None:
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
    # 발음 / 発音
    if msg.startswith("발음 ") or msg.startswith("発音 "):
        rest = re.sub(r"^(발음|発音)\s+", "", msg)
        ko, ja = (s.strip() for s in rest.split("|", 1)) if "|" in rest else (rest, rest)
        return [build.pronunciation(ko, ja)]

    # 예문 / 例文
    if msg.startswith("예문 ") or msg.startswith("例文 "):
        rest = re.sub(r"^(예문|例文)\s+", "", msg)
        ko, ja = (s.strip() for s in rest.split("|", 1)) if "|" in rest else (rest, rest)
        return build.example_card(ko, ja, fetch_example(ja))

    # 단어 데이터 미로드
    if not lexicon.JLPT_WORDS:
        return build.no_data()

    # 단어 / 単語
    if "단어" in msg or "単語" in msg or "たんご" in msg:
        count = parse_request_count(msg)
        level = _parse_level_ja(msg)
        pairs = pick_random_words(count, level)
        return build.word_list(pairs, level, count)

    # 퀴즈 / クイズ
    if msg in ("퀴즈", "クイズ", "다음 문제", "次の問題") \
            or re.match(r"^(초급|중급|고급) 퀴즈$", msg) \
            or re.match(r"^(初級|中級|上級)クイズ$", msg):
        level = _parse_level_ja(msg)
        quiz  = generate_quiz(level)
        if not quiz:
            return build.no_data()
        return build.quiz_question(quiz)

    # 내 점수 / スコア
    if msg in ("내 점수", "점수", "スコア", "得点", "スコアを見る"):
        return build.format_stats(get_user_stats(uid))

    # 퀴즈 정답 처리 (내부 포맷, 버튼에서 자동 전송)
    if msg.startswith("퀴즈답 "):
        parts = msg[4:].strip().split("|")
        if len(parts) == 3:
            ko, correct_ja, chosen_ja = parts
            is_correct = check_answer(correct_ja, chosen_ja)
            save_quiz_result(uid, is_correct, ko, correct_ja, "")
            return build.quiz_result(is_correct, ko, correct_ja)

    # 기본 에코
    return build.echo(msg)


def _parse_level_ja(msg: str) -> str | None:
    """일본어 + 한국어 레벨 키워드 파싱"""
    level_map = {
        "초급": "초급", "쉬운": "초급", "初級": "초급",
        "중급": "중급", "보통": "중급", "中級": "중급",
        "고급": "고급", "어려운": "고급", "上級": "고급",
    }
    for key, lv in level_map.items():
        if key in msg:
            return lv
    return None
