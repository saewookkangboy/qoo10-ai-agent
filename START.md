# 로컬 서비스 실행 방법

## 1. 백엔드 (API 서버)

**프로젝트 루트**에서 실행 (qoo10-ai-agent 폴더):

```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

또는 이미 루트에 있다면:

```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

- 주소: http://localhost:8080  
- API 문서: http://localhost:8080/docs  
- (기본 포트는 `main.py`의 PORT 기본값 8080과 동일합니다. 8000으로 쓰려면 프론트엔드 `.env`에 `VITE_API_URL=http://localhost:8000` 설정)  

## 2. 프론트엔드 (Vite 개발 서버)

**새 터미널**에서 (프로젝트 루트: qoo10-ai-agent):

```bash
cd /Users/chunghyo/qoo10-ai-agent/frontend
npm run dev
```

또는 `frontend` 폴더에 있다면 그대로 `npm run dev` 만 실행하면 됩니다.

- 브라우저에서 **Vite가 안내하는 주소**로 접속 (예: http://localhost:3000)
- 프론트는 `/api`, `/health` 요청을 백엔드(8080)로 프록시합니다.

## 3. 한 번에 확인

- 백엔드: http://localhost:8080/health → `{"status":"healthy"}`
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
  → 백엔드를 먼저 실행했는지 확인. 기본 포트 8080에서 떠 있어야 합니다.

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

- **"API 서버 URL이 설정되지 않았습니다" (Vercel 배포 후)**  
  → Vercel 대시보드 → 해당 프론트 프로젝트 → **Settings** → **Environment Variables**에서 **VITE_API_URL**을 추가하고, 백엔드 URL(예: `https://your-api.railway.app` 또는 API 전용 Vercel URL)을 넣은 뒤 **재배포**하세요.  
  → 로컬에서 **localhost**로 열면 `VITE_API_URL` 없이도 기본값 `http://localhost:8080`이 사용됩니다.

- **WebSocket connection to 'ws://localhost:8081/' failed**  
  → Cursor 내장 미리보기(8081) 등에서 나올 수 있는 메시지입니다. **기능에는 영향 없습니다.**  
  → 브라우저에서 직접 **http://localhost:3000** 으로 접속하면 해당 경고가 없을 수 있습니다.

## Git 워크플로우

- **팀 정책:** **main** 및 **dev**에는 직접 푸시할 수 없습니다. 모든 변경은 **Pull Request**를 통해서만 반영합니다.
- **금지:** `main` 또는 `dev`를 로컬에서 병합한 뒤 `git push origin main`(또는 `dev`) 하는 행위. 브랜치 보호가 켜져 있으면 푸시가 거부됩니다.
- **필수 절차**
  1. 작업은 **feature 브랜치**에서 진행하고 원격에 푸시합니다.
  2. **main** 또는 **dev**를 대상으로 **Pull Request**를 연다.
  3. **CI가 통과**하고 **리뷰 승인**된 뒤에만 PR을 머지합니다. 머지는 GitHub UI에서 수행합니다.
- **브랜치 이름 예시 (권장):** `feat/상세이미지-추출`, `feat/vercel-deploy`, `fix/placeholder-handling`, `p-work/분석-저장` 등. (`feat/*`, `fix/*`, `p-work/*` 패턴 사용 권장.)
- **요약:** 로컬에서 main/dev로의 merge는 하지 말고, feature 브랜치 → PR 생성 → CI 및 리뷰 통과 → PR 머지 순서로 진행합니다.
