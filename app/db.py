# -*- coding: utf-8 -*-
# Supabase 클라이언트 + 퀴즈 결과 저장/조회

import os
from supabase import create_client, Client

_client: Client | None = None


def get_client() -> Client | None:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key:
            _client = create_client(url, key)
    return _client


def save_quiz_result(user_id: str, correct: bool, word_ko: str, word_ja: str, level: str) -> None:
    db = get_client()
    if not db:
        return
    try:
        db.table("quiz_results").insert({
            "user_id": user_id,
            "correct": correct,
            "word_ko": word_ko,
            "word_ja": word_ja,
            "level": level,
        }).execute()
    except Exception as e:
        print(f"[db] 저장 실패: {e}")


def get_user_stats(user_id: str) -> dict:
    db = get_client()
    if not db:
        return {}
    try:
        res = db.table("quiz_results") \
            .select("correct") \
            .eq("user_id", user_id) \
            .execute()
        rows = res.data or []
        total   = len(rows)
        correct = sum(1 for r in rows if r["correct"])
        return {"total": total, "correct": correct}
    except Exception as e:
        print(f"[db] 조회 실패: {e}")
        return {}
