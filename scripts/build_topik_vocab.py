# -*- coding: utf-8 -*-
"""
TOPIK 단어 리스트(GitHub) + Google Translate → words_ja_ko_JLPT.json 생성
"""
import json, time, requests
from deep_translator import GoogleTranslator

TOPIK_TSV_URL = (
    "https://raw.githubusercontent.com/julienshim/combined_korean_vocabulary_list"
    "/master/results.tsv"
)
CHUNK = 50  # 한 번에 번역할 단어 수 (줄바꿈으로 구분)

def fetch_topik_words() -> list[str]:
    print("TOPIK 단어 다운로드 중...")
    r = requests.get(TOPIK_TSV_URL, timeout=15)
    r.raise_for_status()
    lines = r.text.splitlines()
    KEEP_POS = {"명사", "동사", "형용사", "부사", "대명사"}
    words = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        word = parts[1].strip()
        pos  = parts[2].strip()
        if word and pos in KEEP_POS and not word.startswith("-"):
            words.append(word)
    seen, unique = set(), []
    for w in words:
        if w not in seen:
            seen.add(w); unique.append(w)
    print(f"  {len(unique)}개 단어 로드")
    return unique

def translate_batch(words: list[str]) -> list[tuple[str, str]]:
    translator = GoogleTranslator(source="ko", target="ja")
    results = []
    total = len(words)
    for i in range(0, total, CHUNK):
        chunk = words[i:i+CHUNK]
        text  = "\n".join(chunk)
        try:
            translated = translator.translate(text)
            ja_list = translated.split("\n")
            if len(ja_list) == len(chunk):
                for ko, ja in zip(chunk, ja_list):
                    results.append((ko, ja.strip()))
            else:
                # 청크 크기 불일치 시 개별 번역으로 폴백
                for ko in chunk:
                    try:
                        results.append((ko, translator.translate(ko)))
                    except:
                        pass
        except Exception as e:
            print(f"  청크 [{i}~{i+CHUNK}] 실패: {e}")
        if (i // CHUNK + 1) % 5 == 0:
            print(f"  {min(i+CHUNK, total)}/{total} 완료...")
            time.sleep(0.5)
    return results

def main():
    words = fetch_topik_words()

    # JLPT 기존 단어 로드 (git에서)
    import subprocess, io
    jlpt_json = subprocess.check_output(
        ["git", "show", "HEAD:words_ja_ko_JLPT.json"],
        cwd="/Users/TEFR/kakaoChatbot"
    )
    jlpt_words = list(json.loads(jlpt_json).values())[0]
    jlpt_ko_set = {pair[0] for pair in jlpt_words}
    print(f"기존 JLPT 단어: {len(jlpt_words)}개")

    # JLPT에 없는 TOPIK 단어만 번역
    new_words = [w for w in words if w not in jlpt_ko_set]
    print(f"새로 번역할 단어: {len(new_words)}개")

    pairs = translate_batch(new_words)

    # 합치기 (JLPT 우선)
    merged = jlpt_words + [[ko, ja] for ko, ja in pairs]
    out = {"JLPT단어": merged}
    out_path = "/Users/TEFR/kakaoChatbot/words_ja_ko_JLPT.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\n완료! 총 {len(merged)}개 단어 저장 → {out_path}")

if __name__ == "__main__":
    main()
