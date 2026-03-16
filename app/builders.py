# -*- coding: utf-8 -*-
# 카카오 응답 JSON 빌더들

from typing import List, Tuple

def build_peritem_carousel_outputs(pairs: List[Tuple[str, str]]) -> list:
    """
    각 단어(한국어, 일본어)를 basicCard 1장으로 만들어 캐러셀에 담아 반환.
    - 캐러셀 1개에 최대 10장 권장 → 초과 시 여러 캐러셀로 분할
    - 각 카드에 '발음 듣기' / '예문 보기' 버튼 추가
    """
    outputs = []
    CHUNK = 10
    for i in range(0, len(pairs), CHUNK):
        items = []
        for ko, ja in pairs[i:i+CHUNK]:
            items.append({
                "title": ko,
                "description": ja,
                "buttons": [
                    {"action": "message", "label": "🔊 발음 듣기", "messageText": f"발음 {ja}"},
                    {"action": "message", "label": "📝 예문 보기", "messageText": f"예문 {ko}|{ja}"}
                ]
            })
        outputs.append({"carousel": {"type": "basicCard", "items": items}})
    return outputs

def build_simplespeech(text: str) -> dict:
    """
    발음만 들려주기(해당 텍스트만). simpleText도 함께 내려 폴백 보장.
    """
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": text}},
                {"simpleSpeech": {"value": text, "lang": "ja"}}
            ]
        }
    }
