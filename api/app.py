"""
Vercel Serverless 진입점.
Vercel이 FastAPI 앱을 인식하도록 app 인스턴스를 노출합니다.
"""
from main import app

__all__ = ["app"]
