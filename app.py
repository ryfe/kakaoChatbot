from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/kakao", methods=["POST"])
def kakao_webhook():
    """
    카카오 i 오픈빌더 → 이 엔드포인트로 POST 요청
    """
    body = request.get_json()
    user_msg = body['userRequest']['utterance'].strip()

    # 사용자 입력에 따라 간단한 로직
    if "안녕하세요" in user_msg:
        reply_text = "안녕하세요! 만나서 반가워요 😄"
    else:
        reply_text = f"당신이 보낸 메시지: {user_msg}"

    # 오픈빌더 응답 JSON (버전 2.0)
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": reply_text
                    }
                }
            ]
        }
    }

    return jsonify(response)

if __name__ == "__main__":
    # 로컬 테스트 시 포트 5000에서 실행
    app.run(host="0.0.0.0", port=5000)