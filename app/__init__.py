# -*- coding: utf-8 -*-
from flask import Flask
from .config import Config
from dotenv import load_dotenv
load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["JSON_AS_ASCII"] = False

    from .kakao import bp as kakao_bp
    app.register_blueprint(kakao_bp)

    from .lexicon import try_load_into_cache
    try_load_into_cache(app)

    return app
