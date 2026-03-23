# -*- coding: utf-8 -*-
# LINE Messaging API 응답 포맷 빌더

from ..core.vocab import romanize


def _qr(label: str, text: str) -> dict:
    """LINE quick reply item"""
    return {
        "type": "action",
        "action": {"type": "message", "label": label, "text": text}
    }


def text(msg: str) -> dict:
    return {"type": "text", "text": msg}


def text_with_replies(msg: str, replies: list[tuple[str, str]]) -> dict:
    """replies: [(label, messageText), ...]"""
    return {
        "type": "text",
        "text": msg,
        "quickReply": {"items": [_qr(lbl, txt) for lbl, txt in replies]},
    }


# ── 단어 ────────────────────────────────────────────────────

def pronunciation(ko: str, ja: str) -> dict:
    roman = romanize(ko)
    return text(f"{ko}\n[{roman}]\n{ja}")


def word_list(pairs: list, level: str | None, count: int) -> list[dict]:
    """단어 목록 → LINE 메시지 리스트 (최대 5개씩 텍스트로)"""
    lines = [f"{ko} [{romanize(ko)}] — {ja}" for ko, ja, *_ in pairs]
    body  = "\n".join(f"{i+1}. {l}" for i, l in enumerate(lines))

    level_label = f"{level} " if level else ""
    msg_with_replies = text_with_replies(
        body,
        [
            ("다시 생성", f"{level_label}단어 {count}개"),
            ("초급",     f"초급 단어 {count}개"),
            ("중급",     f"중급 단어 {count}개"),
            ("고급",     f"고급 단어 {count}개"),
        ]
    )
    return [msg_with_replies]


# ── 예문 ────────────────────────────────────────────────────

def example_card(ko_word: str, ja_word: str, example: dict | None) -> list[dict]:
    if not example:
        return [text(f"'{ja_word}'(으)로 예문을 찾지 못했어요.")]
    body = f"예문: {ko_word} — {ja_word}\n\n{example['ja_sent']}\n{example['ko_sent']}"
    if example.get("url"):
        body += f"\n\n🔗 {example['url']}"
    return [text(body)]


# ── 퀴즈 ────────────────────────────────────────────────────

def quiz_question(quiz: dict) -> list[dict]:
    ko, correct_ja, options = quiz["ko"], quiz["correct_ja"], quiz["options"]
    return [text_with_replies(
        f"「{ko}」의 일본어는?",
        [(ja, f"퀴즈답 {ko}|{correct_ja}|{ja}") for ja in options]
    )]


def quiz_result(is_correct: bool, ko: str, correct_ja: str) -> list[dict]:
    msg = f"✅ 정답!\n「{ko}」= {correct_ja}" if is_correct \
        else f"❌ 오답\n「{ko}」의 일본어는 {correct_ja}"
    return [text_with_replies(msg, [
        ("다음 문제", "퀴즈"),
        ("점수",     "내 점수"),
        ("단어 보기", "한국어 단어 5개"),
    ])]
