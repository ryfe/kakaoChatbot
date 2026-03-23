# -*- coding: utf-8 -*-
# LINE Messaging API 응답 포맷 빌더 (일본어 UI)

from ..core.vocab import romanize


def _qr(label: str, text: str) -> dict:
    return {
        "type": "action",
        "action": {"type": "message", "label": label, "text": text}
    }


def text(msg: str) -> dict:
    return {"type": "text", "text": msg}


def text_with_replies(msg: str, replies: list[tuple[str, str]]) -> dict:
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
    level_ja = {"초급": "初級", "중급": "中級", "고급": "上級"}.get(level or "", "")
    title = f"📚 韓国語単語" + (f"  {level_ja}" if level_ja else "")

    rows = []
    for i, (ko, ja, *_) in enumerate(pairs):
        if i > 0:
            rows.append({"type": "separator", "margin": "sm"})
        rows.append({
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "contents": [
                {"type": "text", "text": ko, "flex": 3, "size": "md", "color": "#333333", "weight": "bold"},
                {"type": "text", "text": ja, "flex": 2, "size": "md", "color": "#666666", "align": "end"},
            ]
        })

    flex_msg = {
        "type": "flex",
        "altText": title,
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#FFE500",
                "contents": [{"type": "text", "text": title, "weight": "bold", "size": "lg", "color": "#333333"}]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": rows,
            }
        },
        "quickReply": {
            "items": [
                _qr("もう一度", f"{level + ' ' if level else ''}단어 {count}개"),
                _qr("初級", f"초급 단어 {count}개"),
                _qr("中級", f"중급 단어 {count}개"),
                _qr("上級", f"고급 단어 {count}개"),
            ]
        }
    }
    return [flex_msg]


# ── 예문 ────────────────────────────────────────────────────

def example_card(ko_word: str, ja_word: str, example: dict | None) -> list[dict]:
    if not example:
        return [text(f"「{ja_word}」の例文が見つかりませんでした。")]
    body = f"例文: {ko_word} — {ja_word}\n\n{example['ja_sent']}\n{example['ko_sent']}"
    if example.get("url"):
        body += f"\n\n🔗 {example['url']}"
    return [text(body)]


# ── 퀴즈 ────────────────────────────────────────────────────

def quiz_question(quiz: dict) -> list[dict]:
    ko, correct_ja, options = quiz["ko"], quiz["correct_ja"], quiz["options"]
    return [text_with_replies(
        f"「{ko}」の日本語は？",
        [(ja, f"퀴즈답 {ko}|{correct_ja}|{ja}") for ja in options]
    )]


def quiz_result(is_correct: bool, ko: str, correct_ja: str) -> list[dict]:
    msg = f"✅ 正解！\n「{ko}」= {correct_ja}" if is_correct \
        else f"❌ 不正解\n「{ko}」の日本語は {correct_ja}"
    return [text_with_replies(msg, [
        ("次の問題", "퀴즈"),
        ("スコア",   "내 점수"),
        ("単語を見る", "한국어 단어 5개"),
    ])]


# ── 점수 ────────────────────────────────────────────────────

def format_stats(stats_dict: dict) -> list[dict]:
    if not stats_dict or stats_dict.get("total", 0) == 0:
        return [text("まだクイズの記録がありません。\n「クイズ」と送って始めてみましょう！")]
    rate = int(stats_dict["correct"] / stats_dict["total"] * 100)
    msg = (
        f"📊 クイズ成績\n"
        f"正解: {stats_dict['correct']} / {stats_dict['total']}問\n"
        f"正答率: {rate}%"
    )
    return [text(msg)]


# ── 에러 / 기타 ─────────────────────────────────────────────

def no_data() -> list[dict]:
    return [text("単語データが読み込まれていません。")]


def echo(msg: str) -> list[dict]:
    return [text(f"受信したメッセージ: {msg}")]
