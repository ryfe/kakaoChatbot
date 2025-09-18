# -*- coding: utf-8 -*-
# Gunicorn 진입점: "gunicorn wsgi:app" 으로 실행

from app import create_app
app = create_app()

if __name__ == "__main__":
    # 로컬 실행용
    app.run(host="0.0.0.0", port=5000)
