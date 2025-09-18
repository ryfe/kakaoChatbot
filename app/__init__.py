# -*- coding: utf-8 -*-
# Flask 앱 팩토리: 설정 적용 + 블루프린트 등록 + JSON 프리로드

from flask import Flask
from .config import Config

def create_app() -> Flask:
    """
    Flask 애플리케이션 생성 함수(앱 팩토리 패턴).
    Render/Gunicorn에서 'wsgi:app' 형태로 사용.
    """
    app = Flask(__name__)

    # 기본 설정 로드 (JSON 경로/HTTP 타임아웃 등)
    app.config.from_object(Config)

    # 한글/일본어가 \uXXXX로 이스케이프되지 않도록 설정
    app.config['JSON_AS_ASCII'] = False

    # 블루프린트 등록
    from .routes.kakao import bp as kakao_bp
    app.register_blueprint(kakao_bp)

    # 서버 시작 시 단어 JSON 미리 로딩(콜드스타트 단축)
    from .services.lexicon import try_load_into_cache
    try_load_into_cache(app)

    return app
