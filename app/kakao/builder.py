# -*- coding: utf-8 -*-
# 카카오 응답 포맷 빌더

from ..core.vocab import romanize

_SHOW = "https://tatoeba.org/en/sentences/show"


# ── 기본 빌더 ────────────────────────────────────────────────

def simple(text: str) -> dict:
    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": text}}]}}


def simple_with_replies(text: str, quick_replies: list) -> dict:
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": text}}],
            "quickReplies": quick_replies,
        }
    }


# ── 단어 ────────────────────────────────────────────────────

def pronunciation(ko: str, ja: str) -> dict:
    roman = romanize(ko)
    return simple(f"{ko}\n[{roman}]\n{ja}")


def word_carousel(pairs: list, level: str | None, count: int) -> dict:
    """단어 쌍 → 캐러셀 (10장 단위 분할)"""
    outputs = []
    for i in range(0, len(pairs), 10):
        items = [
            {
                "title": f"{ko} [{romanize(ko)}]",
                "description": ja,
                "buttons": [
                    {"action": "message", "label": "📝 예문 보기",
                     "messageText": f"예문 {ko}|{ja}"}
                ]
            }
            for ko, ja, *_ in pairs[i:i + 10]
        ]
        outputs.append({"carousel": {"type": "basicCard", "items": items}})

    level_label = f"{level} " if level else ""
    return {
        "version": "2.0",
        "template": {
            "outputs": outputs,
            "quickReplies": [
                {"label": "다시 생성", "action": "message",
                 "messageText": f"{level_label}단어 {count}개"},
                {"label": "초급", "action": "message",
                 "messageText": f"초급 단어 {count}개"},
                {"label": "중급", "action": "message",
                 "messageText": f"중급 단어 {count}개"},
                {"label": "고급", "action": "message",
                 "messageText": f"고급 단어 {count}개"},
            ]
        }
    }


# ── 예문 ────────────────────────────────────────────────────

def example_card(ko_word: str, ja_word: str, example: dict | None) -> dict:
    if not example:
        return {
            "version": "2.0",
            "template": {"outputs": [{"basicCard": {
                "title": "예문 없음",
                "description": f"'{ja_word}'(으)로 예문을 찾지 못했어요.",
            }}]}
        }
    card = {
        "title": f"예문: {ko_word} — {ja_word}",
        "description": f"{example['ja_sent']}\n{example['ko_sent']}",
    }
    if example.get("url"):
        card["buttons"] = [{"action": "webLink", "label": "원문 보기",
                            "webLinkUrl": example["url"]}]
    return {"version": "2.0", "template": {"outputs": [{"basicCard": card}]}}


# ── 퀴즈 ────────────────────────────────────────────────────

def quiz_question(quiz: dict) -> dict:
    """퀴즈 데이터 → 카카오 응답"""
    ko, correct_ja, options = quiz["ko"], quiz["correct_ja"], quiz["options"]
    quick_replies = [
        {"label": ja, "action": "message",
         "messageText": f"퀴즈답 {ko}|{correct_ja}|{ja}"}
        for ja in options
    ]
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": f"「{ko}」의 일본어는?"}}],
            "quickReplies": quick_replies,
        }
    }


def quiz_result(is_correct: bool, ko: str, correct_ja: str) -> dict:
    msg = f"✅ 정답!\n「{ko}」= {correct_ja}" if is_correct \
        else f"❌ 오답\n「{ko}」의 일본어는 {correct_ja}"
    return simple_with_replies(msg, [
        {"label": "다음 문제", "action": "message", "messageText": "퀴즈"},
        {"label": "점수",     "action": "message", "messageText": "내 점수"},
        {"label": "단어 보기", "action": "message", "messageText": "한국어 단어 5개"},
    ])
