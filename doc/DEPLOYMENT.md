# Vercel 배포 가이드

이 문서는 **프론트엔드**와 **API(백엔드)** 를 Vercel에 배포하는 방법을 안내합니다. dev-agent-kit 워크플로우에 맞춰 분석 결과 저장 및 AI 강화학습 데이터 수집이 동작하도록 구성합니다.

---

## A. 프론트엔드 배포 (Vite)

> **필수:** 프론트엔드만 배포하는 Vercel 프로젝트는 반드시 **Root Directory를 `frontend`로 설정**하세요.  
> 루트로 두면 저장소의 `api/` 폴더가 Vercel 서버리스 함수로 인식되어 `api/requirements.txt`(torch, playwright 등)가 설치되며, 번들이 **500MB 제한을 초과**해 빌드가 실패합니다.

## 1. Vercel 프로젝트 생성

### 1.1 Vercel 계정 준비
1. [Vercel](https://vercel.com)에 로그인 또는 회원가입
2. GitHub 계정으로 연동 (권장)

### 1.2 프로젝트 연결
1. Vercel 대시보드에서 "Add New Project" 클릭
2. GitHub 저장소 선택
3. 프로젝트 설정 (프론트엔드 전용이면 **Root Directory 필수**):
   - **Root Directory**: **`frontend`** (반드시 설정. 비워 두면 `api/` 번들로 500MB 초과 에러 발생)
   - **Framework Preset**: Vite (자동 감지)
   - **Build Command**: `npm run build` (자동 감지)
   - **Output Directory**: `dist` (자동 감지)
   - **Install Command**: `npm install` (자동 감지)

### 1.3 환경 변수 설정
Vercel 대시보드 → 프로젝트 → Settings → Environment Variables에서 추가:

```
VITE_API_URL=https://your-api-domain.vercel.app
```

> **중요**: API를 먼저 배포한 뒤 해당 URL을 설정하거나, Railway 등 별도 백엔드 URL을 사용할 수 있습니다.

### 1.4 배포
- Vercel은 GitHub에 푸시할 때마다 자동으로 배포합니다
- 또는 Vercel 대시보드에서 "Deploy" 버튼 클릭

## 2. 배포 확인

### 2.1 배포 상태 확인
- Vercel 대시보드 → Deployments 탭에서 배포 상태 확인
- 성공적으로 배포되면 URL이 생성됩니다

### 2.2 기능 테스트
1. 배포된 URL 접속
2. Qoo10 URL 입력하여 분석 기능 테스트
3. 브라우저 개발자 도구에서 네트워크 오류 확인

## 3. 커스텀 도메인 설정 (선택사항)

1. Vercel 프로젝트 → Settings → Domains
2. 원하는 도메인 입력
3. DNS 설정 안내에 따라 도메인 설정

## 4. 환경 변수 업데이트

백엔드 URL이 변경되면:
1. Vercel 대시보드 → Settings → Environment Variables
2. `VITE_API_URL` 값 업데이트
3. 자동으로 재배포됩니다

## 5. 문제 해결

### 5.1 빌드 실패
- Vercel 로그 확인: Deployments → 해당 배포 → Logs
- 로컬에서 `npm run build` 테스트
- `package.json`의 의존성 확인

### 5.2 API 연결 오류
- `VITE_API_URL` 환경 변수가 올바른지 확인
- CORS 설정 확인 (백엔드)
- 브라우저 개발자 도구에서 네트워크 탭 확인

### 5.3 라우팅 오류 (404)
- `vercel.json`의 `rewrites` 설정 확인
- SPA 라우팅이 올바르게 설정되었는지 확인

### 5.4 "Total dependency size exceeds 500 MB" / Lambda ephemeral storage limit
- **원인**: 프로젝트 Root Directory가 저장소 루트로 되어 있어, `api/` 폴더가 서버리스 함수로 묶이고 `api/requirements.txt` 의존성(torch, playwright 등)이 전부 설치됨.
- **해결**: Vercel → **Settings** → **General** → **Root Directory**를 **`frontend`**로 설정 후 **Save**하고 재배포. (프론트만 배포하는 프로젝트는 반드시 Root Directory = `frontend`.)

---

## B. API(백엔드) 배포 (FastAPI on Vercel)

서버리스 환경에서는 **요청 간 메모리가 공유되지 않으므로** 분석 결과는 반드시 DB에 저장해야 합니다. 결과 조회·다운로드·채팅은 `analysis_store`에 없을 때 DB 히스토리에서 조회합니다.

### B.1 사전 요구사항

- **데이터베이스**: Vercel에서는 로컬 파일 시스템이 읽기 전용이므로 **SQLite 사용 불가**. **PostgreSQL 필수**.
  - [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres) 또는
  - [Supabase](https://supabase.com), Railway Postgres 등 외부 Postgres 권장
- `api/.env` 또는 Vercel 환경 변수에 `DATABASE_URL=postgresql://...` 설정

### B.2 Vercel에 API 프로젝트 연결

1. Vercel 대시보드 → "Add New Project" → 동일 GitHub 저장소 선택
2. **Root Directory**: `api` 로 설정 (프론트엔드와 별도 프로젝트로 배포)
3. **Framework Preset**: Vercel이 FastAPI를 자동 감지 (진입점: `app.py` → `from main import app`)
4. **Build / Install**: `pip install -r requirements.txt` (자동 처리됨)

### B.3 API 프로젝트 환경 변수

Vercel → 해당 API 프로젝트 → Settings → Environment Variables:

| 변수명 | 설명 | 필수 |
|--------|------|------|
| `DATABASE_URL` | Postgres 연결 URL | ✅ |
| `GEMINI_API_KEY` 또는 `OPENAI_API_KEY` | AI 분석용 | 권장 |
| `ALLOWED_ORIGINS` | CORS (예: `https://프론트도메인.vercel.app`) | 권장 |
| `ENABLE_LEARNING_TRAJECTORY` | AI 강화학습 trajectory 저장 (1/0) | 선택(기본 1) |

### B.4 제한 사항

- **실행 시간**: 함수 최대 실행 시간(기본 10초, Pro 60초). 장시간 분석은 타임아웃 가능성이 있으므로 모니터링 권장.
- **번들 크기**: 500MB 제한. `requirements.txt`의 불필요 패키지는 제거해 두는 것이 좋습니다.

### B.5 로컬에서 Vercel API 테스트

```bash
cd api
pip install -r requirements.txt
vercel dev
```

---

## 참고 자료

- [Vercel 문서](https://vercel.com/docs)
- [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi)
- [Vite 배포 가이드](https://vitejs.dev/guide/static-deploy.html)
