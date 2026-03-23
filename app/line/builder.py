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
        roman = romanize(ko)
        rows.append({
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "action": {"type": "message", "text": f"예문 {ko}|{ja}"},
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 3,
                    "contents": [
                        {"type": "text", "text": ko, "size": "md", "color": "#333333", "weight": "bold"},
                        {"type": "text", "text": roman, "size": "xs", "color": "#999999"},
                    ]
                },
                {"type": "text", "text": ja, "flex": 2, "size": "md", "color": "#666666", "align": "end", "gravity": "center"},
                {"type": "text", "text": "›", "size": "lg", "color": "#CCCCCC", "gravity": "center", "flex": 0},
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
    roman = romanize(ko_word)
    contents = [
        {"type": "box", "layout": "horizontal", "contents": [
            {"type": "text", "text": ko_word, "weight": "bold", "size": "lg", "color": "#333333", "flex": 3},
            {"type": "text", "text": ja_word, "size": "md", "color": "#666666", "flex": 2, "align": "end", "gravity": "center"},
        ]},
        {"type": "text", "text": roman, "size": "xs", "color": "#999999", "margin": "xs"},
        {"type": "separator", "margin": "md"},
        {"type": "text", "text": example["ko_sent"], "size": "md", "color": "#333333", "margin": "md", "wrap": True},
        {"type": "text", "text": example["ja_sent"], "size": "sm", "color": "#666666", "margin": "sm", "wrap": True},
    ]
    if example.get("url"):
        contents.append({
            "type": "text", "text": "Tatoeba で見る →", "size": "xs",
            "color": "#0078D7", "margin": "md",
            "action": {"type": "uri", "uri": example["url"]}
        })
    flex_msg = {
        "type": "flex",
        "altText": f"「{ko_word}」の例文",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#FFE500",
                "contents": [{"type": "text", "text": "💬 例文", "weight": "bold", "size": "lg", "color": "#333333"}]
            },
            "body": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": contents}
        },
        "quickReply": {"items": [
            _qr("もう一度", f"예문 {ko_word}|{ja_word}"),
            _qr("クイズ", "퀴즈"),
            _qr("単語を見る", "한국어 단어 5개"),
        ]}
    }
    return [flex_msg]


# ── 퀴즈 ────────────────────────────────────────────────────

def quiz_question(quiz: dict) -> list[dict]:
    ko, correct_ja, options = quiz["ko"], quiz["correct_ja"], quiz["options"]
    roman = romanize(ko)
    flex_msg = {
        "type": "flex",
        "altText": f"「{ko}」の日本語は？",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#FFE500",
                "contents": [{"type": "text", "text": "🧠 クイズ", "weight": "bold", "size": "lg", "color": "#333333"}]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": ko, "size": "xxl", "weight": "bold", "align": "center", "color": "#333333"},
                    {"type": "text", "text": roman, "size": "sm", "align": "center", "color": "#999999"},
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "日本語はどれ？", "size": "sm", "color": "#666666", "margin": "md", "align": "center"},
                ]
            }
        },
        "quickReply": {
            "items": [_qr(ja, f"퀴즈답 {ko}|{correct_ja}|{ja}") for ja in options]
        }
    }
    return [flex_msg]


def quiz_result(is_correct: bool, ko: str, correct_ja: str) -> list[dict]:
    roman = romanize(ko)
    color = "#00B900" if is_correct else "#E53935"
    header_color = "#E8F5E9" if is_correct else "#FFEBEE"
    icon = "✅ 正解！" if is_correct else "❌ 不正解"
    flex_msg = {
        "type": "flex",
        "altText": icon,
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": header_color,
                "contents": [{"type": "text", "text": icon, "weight": "bold", "size": "lg", "color": color}]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": ko, "size": "xxl", "weight": "bold", "align": "center", "color": "#333333"},
                    {"type": "text", "text": roman, "size": "sm", "align": "center", "color": "#999999"},
                    {"type": "separator", "margin": "md"},
                    {"type": "box", "layout": "horizontal", "margin": "md", "contents": [
                        {"type": "text", "text": "正解", "size": "sm", "color": "#999999", "flex": 1},
                        {"type": "text", "text": correct_ja, "size": "md", "weight": "bold", "color": color, "flex": 2, "align": "end"},
                    ]}
                ]
            }
        },
        "quickReply": {
            "items": [
                _qr("次の問題", "퀴즈"),
                _qr("例文を見る", f"예문 {ko}|{correct_ja}"),
                _qr("スコア",   "내 점수"),
            ]
        }
    }
    return [flex_msg]


# ── 점수 ────────────────────────────────────────────────────

def format_stats(stats_dict: dict) -> list[dict]:
    if not stats_dict or stats_dict.get("total", 0) == 0:
        return [text("まだクイズの記録がありません。\n「クイズ」と送って始めてみましょう！")]
    total   = stats_dict["total"]
    correct = stats_dict["correct"]
    wrong   = total - correct
    rate    = int(correct / total * 100)
    flex_msg = {
        "type": "flex",
        "altText": f"クイズ成績 {rate}%",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#FFE500",
                "contents": [{"type": "text", "text": "📊 クイズ成績", "weight": "bold", "size": "lg", "color": "#333333"}]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {"type": "text", "text": f"{rate}%", "size": "5xl", "weight": "bold", "align": "center", "color": "#333333"},
                    {"type": "separator"},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "正解", "color": "#00B900", "flex": 1},
                        {"type": "text", "text": str(correct), "weight": "bold", "flex": 1, "align": "end"},
                    ]},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "不正解", "color": "#E53935", "flex": 1},
                        {"type": "text", "text": str(wrong), "weight": "bold", "flex": 1, "align": "end"},
                    ]},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "合計", "color": "#666666", "flex": 1},
                        {"type": "text", "text": f"{total}問", "weight": "bold", "flex": 1, "align": "end"},
                    ]},
                ]
            }
        },
        "quickReply": {
            "items": [
                _qr("クイズ", "퀴즈"),
                _qr("単語を見る", "한국어 단어 5개"),
            ]
        }
    }
    return [flex_msg]


# ── 에러 / 기타 ─────────────────────────────────────────────

def no_data() -> list[dict]:
    return [text("単語データが読み込まれていません。")]


def echo(msg: str) -> list[dict]:
    return [text(f"受信したメッセージ: {msg}")]
