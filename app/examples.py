# -*- coding: utf-8 -*-
# Tatoeba API 예문 조회

import requests
from flask import current_app

_API  = "https://tatoeba.org/eng/api_v0/search"
_SHOW = "https://tatoeba.org/en/sentences/show"


def _fetch(ja_query: str) -> tuple[str, str, int] | None:
    """
    Tatoeba에서 일본어 문장 + 한국어 번역 1쌍 조회.
    실제 API 응답: translations은 list of list
      [ [{"id":..,"text":"한국어","lang":"kor"}, ...], ... ]
    """
    params = {
        "from": "jpn", "to": "kor",
        "query": ja_query,
        "trans_filter": "limit", "trans_link": "direct",
        "sort": "relevance", "page": 1,
    }
    try:
        r = requests.get(_API, params=params,
                         timeout=current_app.config.get("HTTP_TIMEOUT", 4.0))
        r.raise_for_status()
        sentences = r.json().get("results") or []
        for s in sentences:
            ja_text = s.get("text") or ""
            sid = s.get("id")
            # translations = list of list; 첫 번째 그룹의 첫 번째 항목
            for group in (s.get("translations") or []):
                for t in group:
                    if t.get("lang") in ("kor", "ko") and t.get("text"):
                        return ja_text, t["text"], sid
    except Exception as e:
        current_app.logger.warning(f"[examples] Tatoeba 호출 실패: {type(e).__name__}")
    return None


def build_example_output_from_api(ko_word: str, ja_word: str) -> dict:
    result = _fetch(ja_word)
    if not result:
        return {
            "version": "2.0",
            "template": {"outputs": [{"basicCard": {
                "title": "예문 없음",
                "description": f"'{ja_word}'(으)로 예문을 찾지 못했어요. 다른 단어로 시도해 주세요."
            }}]}
        }
    ja_sent, ko_sent, sid = result
    card = {
        "title": f"예문: {ko_word} — {ja_word}",
        "description": f"{ja_sent}\n{ko_sent}",
    }
    if sid:
        card["buttons"] = [{"action": "webLink", "label": "원문 보기",
                            "webLinkUrl": f"{_SHOW}/{sid}"}]
    return {"version": "2.0", "template": {"outputs": [{"basicCard": card}]}}
