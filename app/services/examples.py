# -*- coding: utf-8 -*-
# 외부 예문 API(Tatoeba) 호출 + 카드 빌더

import requests
from flask import current_app
from typing import List, Tuple

TATOEBA_API = "https://tatoeba.org/eng/api_v0/search"
TATOEBA_SHOW = "https://tatoeba.org/en/sentences/show"

def fetch_examples_from_tatoeba(ja_query: str, want: int = 1) -> List[Tuple[str, str, int]]:
    """
    Tatoeba에서 일본어 문장 + 한국어 직역 번역을 조회.
    반환: [(ja_sentence, ko_sentence, sentence_id), ...]
    """
    params = {
        "from": "jpn", "query": ja_query, "to": "kor",
        "trans_filter": "limit", "trans_link": "direct", "trans_to": "kor",
        "sort": "relevance", "page": 1
    }
    timeout = current_app.config.get("HTTP_TIMEOUT", 4.0)
    try:
        r = requests.get(TATOEBA_API, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        results = (data.get("results") or {})
        sentences = results.get("sentences") or []
        out: List[Tuple[str, str, int]] = []
        for s in sentences:
            ja_text = s.get("text") or ""
            sid = s.get("id")
            translations = s.get("translations") or {}
            ko_list = translations.get("kor") or translations.get("ko") or []
            ko_text = ko_list[0].get("text") if ko_list else None
            if ja_text and ko_text:
                out.append((ja_text, ko_text, sid))
            if len(out) >= want:
                break
        return out
    except Exception as e:
        current_app.logger.warning(f"[examples] Tatoeba 호출 실패: {type(e).__name__}")
        return []

def build_example_output_from_api(ko_word: str, ja_word: str) -> dict:
    """
    예문 1개를 받아 basicCard JSON으로 구성.
    """
    ex = fetch_examples_from_tatoeba(ja_word, want=1)
    if not ex:
        txt = f"'{ja_word}'(으)로 예문을 찾지 못했어요. 다른 단어로 다시 시도해 주세요."
        return {"version": "2.0", "template": {"outputs": [
            {"basicCard": {"title": "예문 없음", "description": txt}}
        ]}}
    ja_sent, ko_sent, sid = ex[0]
    link = f"{TATOEBA_SHOW}/{sid}" if sid else None
    card = {
        "title": f"예문: {ko_word} — {ja_word}",
        "description": f"{ja_sent}\n{ko_sent}"
    }
    if link:
        card["buttons"] = [{"action": "webLink", "label": "원문 보기", "webLinkUrl": link}]
    return {"version": "2.0", "template": {"outputs": [{"basicCard": card}]}}
