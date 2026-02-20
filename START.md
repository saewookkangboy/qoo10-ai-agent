# 로컬 서비스 실행 방법

## 1. 백엔드 (API 서버)

**프로젝트 루트**에서 실행 (qoo10-ai-agent 폴더):
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd /Users/chunghyo/qoo10-ai-agent/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

또는 이미 루트에 있다면:

```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- 주소: http://localhost:8000  
- API 문서: http://localhost:8000/docs  

## 2. 프론트엔드 (Vite 개발 서버)

**새 터미널**에서 (프로젝트 루트: qoo10-ai-agent):

```bash
cd /Users/chunghyo/qoo10-ai-agent/frontend
npm run dev
```

또는 `frontend` 폴더에 있다면 그대로 `npm run dev` 만 실행하면 됩니다.

- 브라우저에서 **Vite가 안내하는 주소**로 접속 (예: http://localhost:3000)
- 프론트는 `/api`, `/health` 요청을 백엔드(8000)로 프록시합니다.

## 3. 한 번에 확인

- 백엔드: http://localhost:8000/health → `{"status":"healthy"}`
- 프론트: 터미널에 나온 주소(예: http://localhost:3000) 접속

## 선택: 빠른 기동 (임베딩 보완 모델 건너뛰기)

첫 실행 시 보완 임베딩 모델(~1.1GB) 다운로드로 기동이 오래 걸리면, `api/.env`에 다음을 추가하면 BGE-M3만 사용해 빨리 뜹니다.

```bash
EMBEDDING_ENSEMBLE=0
```

## 선택: Playwright 브라우저 설치 (크롤링 품질 향상)

`Executable doesn't exist at .../chromium_headless_shell` 오류가 나면 브라우저가 미설치된 것입니다. 설치하면 Playwright 크롤링이 동작하고, 없으면 HTTP 크롤링만 사용됩니다(데이터가 불완전할 수 있음).

```bash
cd /Users/chunghyo/qoo10-ai-agent/api
playwright install chromium
```

또는 `python -m playwright install chromium`

## 문제 해결

- **"API 서버에 연결할 수 없습니다"**  
  → 백엔드를 먼저 실행했는지 확인. 포트 8000에서 떠 있어야 합니다.

- **ERR_CONNECTION_REFUSED (localhost:3000)**  
  → **프론트엔드가 꺼져 있습니다.** 새 터미널에서 실행하세요:
  ```bash
  cd /Users/chunghyo/qoo10-ai-agent/frontend
  npm run dev
  ```
  그 다음 브라우저에서 터미널에 나온 주소(예: http://localhost:3000)로 접속하세요.

- **WebSocket / ping to localhost:3000 failed**  
  → 위와 동일. 프론트 dev 서버를 켜면 해결됩니다.

- 백엔드를 **다른 포트**(예: 8080)에서 쓰는 경우  
  → `frontend/.env` 파일을 만들고 다음 한 줄 추가:
  ```bash
  VITE_API_PROXY_TARGET=http://localhost:8080
  ```
  저장 후 프론트를 다시 실행하세요.
