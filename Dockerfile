# Qoo10 AI Agent API - Railway 배포용 (저장소 루트에서 api/ 빌드)
FROM python:3.11-slim

WORKDIR /app

# api/ 폴더만 복사 (빌드 컨텍스트는 저장소 루트)
COPY api/ .

RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install chromium

EXPOSE 8080

ENV PORT=8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
