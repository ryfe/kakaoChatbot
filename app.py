# -*- coding: utf-8 -*-
# 카카오 i 오픈빌더 스킬 서버 — JLPT(N4+N5) 통합 JSON 사용 버전
# - 데이터 파일: words_ko_ja_JLPT.json
#   구조 예) { "JLPT단어": [ ["会う","만나다"], ["青い","파랗다. 푸르다"], ... ] }
# - 동작:
#   * "한국어 단어 10개" 같이 개수만 지정하면 JLPT단어 풀에서랜덤 선택
#   * "한국어 단어 15개 여행"처럼 주제를 적어도(현재는) 무시하고 랜덤 추출(필요 시 필터 확장 가능)
# - 외부 API 없음(0원), Render 등 무료 인프라에서 동작
#
# 실행(로컬) : python app.py
# 배포(Render): gunicorn app:app --workers 2 --threads 4 --timeout 60
#
# 환경변수(선택):
#   JLPT_JSON_PATH=./words_ko_ja_JLPT.json   # JSON 경로 변경 시 지정

import os
import re
import json
import random
from typing import List, Tuple
from flask import Flask, request, jsonify

# Flask 애플리케이션 인스턴스(WSGI 진입점)
app = Flask(__name__)

# 통합 JSON 경로 (기본: 프로젝트 루트에 위치)
JLPT_JSON_PATH = os.getenv("JLPT_JSON_PATH", "./words_ja_ko_JLPT.json")

# 메모리 캐시에 단어 목록을 보관
JLPT_WORDS: List[Tuple[str, str]] = []  # [("한국어", "일본어"), ...]

def load_jlpt_words(path: str) -> List[Tuple[str, str]]:
    """
    통합 JSON을 로딩하여 [("한국어", "일본어"), ...] 리스트로 반환.
    - 파일이 없거나 포맷이 다르면 예외 발생(호출부에서 처리).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"통합 JSON을 찾을 수 없습니다: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "JLPT단어" not in data or not isinstance(data["JLPT단어"], list):
        raise ValueError("JSON에 'JLPT단어' 리스트가 없습니다.")

    # 각 항목은 길이 2의 리스트/튜플이어야 함: [ko, ja]
    words: List[Tuple[str, str]] = []
    for item in data["JLPT단어"]:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            ko, ja = str(item[0]), str(item[1])
            words.append((ko, ja))
    if not words:
        raise ValueError("'JLPT단어'에 유효한 항목이 없습니다.")
    return words

def try_load_into_cache() -> None:
    """
    서버 시작 시/리로드 시 통합 JSON을 읽어 JLPT_WORDS에 저장.
    """
    global JLPT_WORDS
    try:
        JLPT_WORDS = load_jlpt_words(JLPT_JSON_PATH)
        app.logger.info(f"통합 단어 로드 완료: {len(JLPT_WORDS)}개 @ {JLPT_JSON_PATH}")
    except Exception as e:
        JLPT_WORDS = []
        app.logger.error(f"통합 단어 로드 실패: {type(e).__name__}: {e}")

@app.route("/health", methods=["GET"])
def health():
    """
    헬스 체크 엔드포인트 — 모니터링/핑 용도(콜드스타트 완화에 유용)
    """
    return "OK", 200

@app.route("/reload", methods=["POST"])
def reload_lexicon():
    """
    (개발 편의) JSON 핫 리로드 엔드포인트.
    운영 시엔 인증/토큰 등을 반드시 붙이는 것을 권장.
    """
    try_load_into_cache()
    msg = (
        f"로드 {'성공' if JLPT_WORDS else '실패'} — "
        f"현재 {len(JLPT_WORDS)}개 단어 @ {JLPT_JSON_PATH}"
    )
    return jsonify({
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": msg}}]}
    }), 200

def parse_request_count(utterance: str) -> int:
    """
    발화에서 '개수'만 추출. (주제는 현재 무시)
    예) '한국어 단어 15개', '한국어 단어 5개 여행' → 15 / 5
    """
    text = utterance.strip() if isinstance(utterance, str) else str(utterance)
    m = re.search(r"(\d+)", text)
    count = int(m.group(1)) if m else 10
    # 과도 방지(가독성/메시지 길이 고려)
    return max(1, min(count, 30))

def pick_random_words(count: int) -> List[Tuple[str, str]]:
    if not JLPT_WORDS:
        return []
    if count >= len(JLPT_WORDS):
        shuffled = JLPT_WORDS[:]
        random.shuffle(shuffled)
        return shuffled[:count]
    return random.sample(JLPT_WORDS, count)

def format_pairs_as_text(pairs: List[Tuple[str, str]]) -> str:
    """
    (한국어, 일본어) 리스트를 카카오 simpleText 형태의 문자열로 변환.
    - "1) 한국어 — 일본어" 번호 목록
    """
    lines = []
    for i, (ko, ja) in enumerate(pairs, start=1):
        if ja:
            lines.append(f"{i}) {ko} — {ja}")
        else:
            lines.append(f"{i}) {ko}")
    text = "\n".join(lines)
    # 너무 길면 일부 생략(대화창 가독성 보호)
    if len(text) > 3500:
        text = text[:3500] + "\n…(일부 생략)"
    return text

def build_listcard_outputs(pairs: List[Tuple[str, str]]):
    """
    Kakao listCard 포맷으로 렌더링(세로 카드).
    - listCard는 items를 최대 5개까지만 지원하므로, 5개 단위로 여러 개의 listCard를 생성.
    - 각 항목: title=한국어, description=일본어
    - 헤더에 페이지 표기 (예: 한국어 — 일본어 (1/3))
    """
    outputs = []
    CHUNK = 5
    total_pages = (len(pairs) + CHUNK - 1) // CHUNK if pairs else 1
    for page, i in enumerate(range(0, len(pairs), CHUNK), start=1):
        chunk = pairs[i:i+CHUNK]
        items = [{"title": ko, "description": ja} for ko, ja in chunk]
        outputs.append({
            "listCard": {
                "header": {"title": f"한국어 — 일본어 ({page}/{total_pages})"},
                "items": items
            }
        })
    return outputs

def build_carousel_outputs(pairs: List[Tuple[str, str]]):
    """
    Kakao carousel + basicCard 포맷(가로 카드, 좌우 스크롤).
    - 5개 단위로 묶어 한 장의 basicCard로 렌더링 → (5,5, ...) 형태로 보임
    - 각 basicCard는 description에 5줄(한국어 — 일본어)을 넣고,
      헤더 용도로 title에 페이지 표기(예: 한국어 — 일본어 (1/2))를 넣는다.
    """
    outputs = []
    CHUNK = 5
    cards = []
    total_pages = (len(pairs) + CHUNK - 1) // CHUNK if pairs else 1
    for page, i in enumerate(range(0, len(pairs), CHUNK), start=1):
        chunk = pairs[i:i+CHUNK]
        # 카드 본문(5줄): "한국어 — 일본어" 형식으로 합침
        desc_lines = [f"{ko} — {ja}" for ko, ja in chunk]
        description = "\n".join(desc_lines)
        cards.append({
            "title": f"한국어 — 일본어 ({page}/{total_pages})",
            "description": description
        })
    # 한 번에 하나의 carousel로 보냄(카카오 권장: items 10개 이하)
    if cards:
        outputs.append({
            "carousel": {
                "type": "basicCard",
                "items": cards
            }
        })
    return outputs

@app.route("/kakao", methods=["POST"])
def kakao_webhook():
    """
    카카오 오픈빌더 스킬 엔드포인트.
    - '한국어 단어' 키워드 포함 시: 통합 JLPT 풀에서 랜덤 추출하여 응답
    - 그 외: 기본 에코(반사) 응답
    - 항상 200 + v2.0 JSON으로 응답해 502/타임아웃을 방지
    """
    try:
        # 요청 JSON 안전 파싱
        body = request.get_json(silent=True) or {}
        utter = (body.get("userRequest", {}) or {}).get("utterance", "")
        user_msg = utter.strip() if isinstance(utter, str) else str(utter)

        # 데이터가 아직 로드되지 않았다면 안내
        if not JLPT_WORDS:
            msg = (
                "단어 데이터가 아직 로드되지 않았습니다.\n"
                f"서버의 JSON 경로를 확인하세요: {JLPT_JSON_PATH}\n"
                "관리자용: /reload 로 JSON을 다시 로드할 수 있습니다."
            )
            return jsonify({
                "version": "2.0",
                "template": {"outputs": [{"simpleText": {"text": msg}}]}
            }), 200

        # 키워드 판별: "한국어 단어"면 단어 생성 로직 실행
        if ("한국어 단어" in user_msg) or ("単語" in user_msg):
            count = parse_request_count(user_msg)
            pairs = pick_random_words(count)
            outputs = build_listcard_outputs(pairs) if len(pairs) <= 5 else build_carousel_outputs(pairs)

            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": outputs,
                    "quickReplies": [
                        {"label": "다시 생성", "action": "message", "messageText": f"한국어 단어 {count}개"},
                        {"label": "5개", "action": "message", "messageText": "한국어 단어 5개"},
                        {"label": "10개", "action": "message", "messageText": "한국어 단어 10개"}
                    ]
                }
            }), 200

        # 기본 반사 응답
        default_text = f"당신이 보낸 메시지: {user_msg}"
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": default_text}}]}
        }), 200

    except Exception as e:
        # 예외가 나도 200으로 안내(오픈빌더가 502로 오해하지 않게)
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": f"처리 중 오류가 발생했어요: {type(e).__name__}"}}]}
        }), 200

# 서버 시작 시 통합 JSON을 미리 로드
try_load_into_cache()

# 로컬 실행 진입점 — Render에서는 gunicorn으로 실행
if __name__ == "__main__":
    # host=0.0.0.0: ngrok/외부 접근 허용
    app.run(host="0.0.0.0", port=5000)