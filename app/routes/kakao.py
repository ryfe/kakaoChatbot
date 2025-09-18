# -*- coding: utf-8 -*-
# /kakao, /health, /reload 라우트

from flask import Blueprint, request, jsonify, current_app
from ..services.lexicon import try_load_into_cache, parse_request_count, pick_random_words, JLPT_WORDS
from ..services.examples import build_example_output_from_api
from ..builders import build_peritem_carousel_outputs, build_simplespeech

bp = Blueprint("kakao", __name__)

@bp.route("/health", methods=["GET"])
def health():
    """헬스 체크 엔드포인트"""
    return "OK", 200

@bp.route("/reload", methods=["POST"])
def reload_lexicon():
    """단어 JSON 핫 리로드(운영 시 인증 권장)"""
    try_load_into_cache()
    msg = (
        f"로드 {'성공' if JLPT_WORDS else '실패'} — "
        f"현재 {len(JLPT_WORDS)}개 단어 @ {current_app.config['JLPT_JSON_PATH']}"
    )
    return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": msg}}]}}), 200

@bp.route("/kakao", methods=["POST"])
def kakao_webhook():
    """
    오픈빌더 스킬 엔드포인트.
    - '한국어 단어' 키워드: 랜덤 추출 + (각 단어 1장) 캐러셀 응답
    - '발음 <일본어>': 해당 텍스트만 TTS/텍스트로 응답
    - '예문 <한국어>|<일본어>': 외부 API로 예문 카드 반환
    """
    try:
        body = request.get_json(silent=True) or {}
        utter = (body.get("userRequest", {}) or {}).get("utterance", "")
        user_msg = utter.strip() if isinstance(utter, str) else str(utter)

        # 0) 빠른 액션 처리
        if user_msg.startswith("발음 "):
            ja_text = user_msg[3:].strip()
            return jsonify(build_simplespeech(ja_text)), 200

        if user_msg.startswith("예문 "):
            rest = user_msg[3:].strip()
            if "|" in rest:
                ko, ja = [s.strip() for s in rest.split("|", 1)]
            else:
                ko, ja = rest, rest  # 한 쪽만 온 경우 폴백
            return jsonify(build_example_output_from_api(ko, ja)), 200

        # 1) 데이터 로드 확인
        if not JLPT_WORDS:
            msg = (
                "단어 데이터가 아직 로드되지 않았습니다.\n"
                f"서버의 JSON 경로를 확인하세요: {current_app.config['JLPT_JSON_PATH']}\n"
                "관리자용: /reload 로 JSON을 다시 로드할 수 있습니다."
            )
            return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": msg}}]}}), 200

        # 2) 키워드 판별 후 단어 생성
        if ("한국어 단어" in user_msg) or ("単語" in user_msg):
            count = parse_request_count(user_msg)
            pairs = pick_random_words(count)
            outputs = build_peritem_carousel_outputs(pairs)
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

        # 3) 기본 에코
        default_text = f"당신이 보낸 메시지: {user_msg}"
        return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": default_text}}]}}), 200

    except Exception as e:
        # 예외가 나도 200으로 안내(오픈빌더가 502로 오해하지 않게)
        return jsonify({"version": "2.0", "template": {"outputs": [
            {"simpleText": {"text": f"처리 중 오류가 발생했어요: {type(e).__name__}"}}]}}), 200
