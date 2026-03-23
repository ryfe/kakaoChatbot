# -*- coding: utf-8 -*-
# Tatoeba API 예문 조회 (플랫폼 독립적)

import requests
from flask import current_app

_API  = "https://tatoeba.org/eng/api_v0/search"
_SHOW = "https://tatoeba.org/en/sentences/show"


def fetch_example(ja_word: str) -> dict | None:
    """
    Tatoeba에서 일본어 문장 + 한국어 번역 조회.
    Returns: {ja_sent, ko_sent, sid, url} or None
    """
    params = {
        "from": "jpn", "to": "kor",
        "query": ja_word,
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
            for group in (s.get("translations") or []):
                for t in group:
                    if t.get("lang") in ("kor", "ko") and t.get("text"):
                        return {
                            "ja_sent": ja_text,
                            "ko_sent": t["text"],
                            "sid": sid,
                            "url": f"{_SHOW}/{sid}" if sid else None,
                        }
    except Exception as e:
        current_app.logger.warning(f"[examples] Tatoeba 호출 실패: {type(e).__name__}")
    return None
