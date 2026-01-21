# 배포 가이드

이 문서는 Qoo10 AI Agent를 Vercel(프론트엔드)과 Railway(백엔드)에 배포하는 방법을 설명합니다.

## 목차

1. [전체 배포 개요](#전체-배포-개요)
2. [Railway 백엔드 배포](#railway-백엔드-배포)
3. [Vercel 프론트엔드 배포](#vercel-프론트엔드-배포)
4. [환경 변수 설정](#환경-변수-설정)
5. [배포 확인 및 테스트](#배포-확인-및-테스트)
6. [문제 해결](#문제-해결)

## 전체 배포 개요

### 아키텍처

```
┌─────────────┐         ┌─────────────┐
│   Vercel    │ ──────> │   Railway   │
│ (Frontend)  │         │  (Backend)  │
│  React App  │         │  FastAPI    │
└─────────────┘         └─────────────┘
```

- **프론트엔드**: Vercel에 배포 (React + Vite)
- **백엔드**: Railway에 배포 (FastAPI + Python)
- **데이터베이스**: Railway PostgreSQL (선택사항)

### 배포 순서

1. Railway에 백엔드 배포
2. Railway URL 확인
3. Vercel에 프론트엔드 배포 (Railway URL 설정)

---

## Railway 백엔드 배포

### 1. Railway 프로젝트 생성

1. [Railway](https://railway.app)에 로그인 또는 회원가입
2. "New Project" 클릭
3. "Deploy from GitHub repo" 선택
4. GitHub 저장소 선택
5. 프로젝트 설정:
   - **Root Directory**: `api`
   - **Build Command**: 자동 감지 (railway.json 사용)
   - **Start Command**: 자동 감지 (railway.json 사용)

### 2. 환경 변수 설정

Railway 대시보드 → 프로젝트 → Variables 탭에서 다음 환경 변수를 설정:

#### 필수 환경 변수

```bash
# 데이터베이스 (PostgreSQL 권장)
DATABASE_URL=postgresql://user:password@host:port/database

# 또는 SQLite 사용 (개발/테스트용)
# DATABASE_URL=sqlite:///crawler_data.db
```

#### 선택적 환경 변수

```bash
# 서버 설정
PORT=8080  # Railway가 자동으로 설정하므로 보통 필요 없음
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,https://your-custom-domain.com

# AI 서비스 API 키 (필요시)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# 임베딩 서비스 설정
EMBEDDING_MODEL=bge-m3
EMBEDDING_ENSEMBLE=1
EMBEDDING_AUTO_LEARN=1

# 크롤러 설정
CRAWLER_DEBUG_LOG=0
PROXY_LIST=  # 프록시 사용 시 설정
```

### 3. PostgreSQL 데이터베이스 추가 (권장)

1. Railway 프로젝트 → "New" → "Database" → "Add PostgreSQL"
2. 생성된 데이터베이스의 `DATABASE_URL`을 복사
3. 환경 변수에 `DATABASE_URL` 설정

### 4. 배포 확인

1. Railway 대시보드 → Deployments 탭에서 배포 상태 확인
2. 배포 완료 후 생성된 URL 확인 (예: `https://your-app-name.railway.app`)
3. 헬스 체크: `https://your-app-name.railway.app/health`
4. API 문서: `https://your-app-name.railway.app/docs`

### 5. CORS 설정

프론트엔드 URL을 `ALLOWED_ORIGINS`에 추가:

```bash
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,https://your-custom-domain.com
```

---

## Vercel 프론트엔드 배포

### 1. Vercel 프로젝트 생성

1. [Vercel](https://vercel.com)에 로그인 또는 회원가입
2. "Add New Project" 클릭
3. GitHub 저장소 선택
4. 프로젝트 설정:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite (자동 감지)
   - **Build Command**: `npm run build` (자동 감지)
   - **Output Directory**: `dist` (자동 감지)
   - **Install Command**: `npm install` (자동 감지)

### 2. 환경 변수 설정

Vercel 대시보드 → 프로젝트 → Settings → Environment Variables에서 추가:

```bash
VITE_API_URL=https://your-railway-backend-url.railway.app
```

> **중요**: Railway 백엔드 배포 후 URL을 설정해야 합니다.

### 3. 배포

- Vercel은 GitHub에 푸시할 때마다 자동으로 배포합니다
- 또는 Vercel 대시보드에서 "Deploy" 버튼 클릭

### 4. 배포 확인

1. Vercel 대시보드 → Deployments 탭에서 배포 상태 확인
2. 배포된 URL 접속하여 기능 테스트
3. 브라우저 개발자 도구에서 네트워크 오류 확인

---

## 환경 변수 설정

### Railway 환경 변수 (백엔드)

Railway 대시보드 → 프로젝트 → Variables에서 설정:

| 변수명 | 설명 | 필수 | 예시 |
|--------|------|------|------|
| `DATABASE_URL` | 데이터베이스 연결 URL | ✅ | `postgresql://user:pass@host:port/db` |
| `ALLOWED_ORIGINS` | CORS 허용 오리진 | ⚠️ | `https://app.vercel.app` |
| `OPENAI_API_KEY` | OpenAI API 키 | ❌ | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | ❌ | `sk-ant-...` |
| `EMBEDDING_MODEL` | 임베딩 모델 | ❌ | `bge-m3` |
| `EMBEDDING_ENSEMBLE` | 앙상블 모드 | ❌ | `1` |
| `EMBEDDING_AUTO_LEARN` | 자동 학습 | ❌ | `1` |

### Vercel 환경 변수 (프론트엔드)

Vercel 대시보드 → 프로젝트 → Settings → Environment Variables에서 설정:

| 변수명 | 설명 | 필수 | 예시 |
|--------|------|------|------|
| `VITE_API_URL` | 백엔드 API URL | ✅ | `https://app.railway.app` |

> **참고**: Vercel 환경 변수는 빌드 시점에 주입되므로, 변경 후 재배포가 필요합니다.

---

## 배포 확인 및 테스트

### 1. 백엔드 확인

```bash
# 헬스 체크
curl https://your-railway-app.railway.app/health

# API 문서 확인
# 브라우저에서 https://your-railway-app.railway.app/docs 접속
```

### 2. 프론트엔드 확인

1. 배포된 URL 접속
2. Qoo10 URL 입력하여 분석 기능 테스트
3. 브라우저 개발자 도구 → Network 탭에서 API 요청 확인
4. Console 탭에서 오류 확인

### 3. 통합 테스트

1. 프론트엔드에서 분석 시작
2. 백엔드 로그 확인 (Railway 대시보드)
3. 분석 결과가 정상적으로 표시되는지 확인

---

## 문제 해결

### 백엔드 배포 문제

#### 빌드 실패

- **원인**: 의존성 설치 실패
- **해결**:
  1. Railway 로그 확인: Deployments → 해당 배포 → Logs
  2. `requirements.txt` 확인
  3. Python 버전 확인 (`runtime.txt`)

#### Playwright 설치 실패

- **원인**: Playwright 브라우저 미설치
- **해결**: `railway.json`의 `buildCommand`에 `playwright install chromium` 추가 (이미 추가됨)

#### 서버 시작 실패

- **원인**: 포트 설정 오류
- **해결**: Railway는 자동으로 `$PORT` 환경 변수를 설정하므로, 코드에서 `$PORT` 사용 확인

#### CORS 오류

- **원인**: `ALLOWED_ORIGINS` 미설정
- **해결**: Railway 환경 변수에 프론트엔드 URL 추가

### 프론트엔드 배포 문제

#### 빌드 실패

- **원인**: 의존성 또는 TypeScript 오류
- **해결**:
  1. Vercel 로그 확인: Deployments → 해당 배포 → Logs
  2. 로컬에서 `npm run build` 테스트
  3. `package.json`의 의존성 확인

#### API 연결 오류

- **원인**: `VITE_API_URL` 미설정 또는 잘못된 URL
- **해결**:
  1. Vercel 환경 변수에서 `VITE_API_URL` 확인
  2. Railway 백엔드 URL이 올바른지 확인
  3. 브라우저 개발자 도구 → Network 탭에서 요청 URL 확인

#### 라우팅 오류 (404)

- **원인**: SPA 라우팅 설정 오류
- **해결**: `vercel.json`의 `rewrites` 설정 확인

### 데이터베이스 연결 문제

#### 연결 실패

- **원인**: `DATABASE_URL` 잘못 설정
- **해결**:
  1. Railway 데이터베이스의 `DATABASE_URL` 확인
  2. 환경 변수에 올바르게 설정되었는지 확인
  3. Railway 로그에서 연결 오류 확인

---

## 추가 리소스

- [Railway 문서](https://docs.railway.app)
- [Vercel 문서](https://vercel.com/docs)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [Vite 배포 가이드](https://vitejs.dev/guide/static-deploy.html)

---

## 배포 체크리스트

### Railway 백엔드

- [ ] Railway 프로젝트 생성
- [ ] GitHub 저장소 연결
- [ ] Root Directory를 `api`로 설정
- [ ] PostgreSQL 데이터베이스 추가 (선택사항)
- [ ] 환경 변수 설정 (`DATABASE_URL`, `ALLOWED_ORIGINS` 등)
- [ ] 배포 완료 확인
- [ ] 헬스 체크 통과 (`/health`)
- [ ] API 문서 접근 가능 (`/docs`)

### Vercel 프론트엔드

- [ ] Vercel 프로젝트 생성
- [ ] GitHub 저장소 연결
- [ ] Root Directory를 `frontend`로 설정
- [ ] 환경 변수 설정 (`VITE_API_URL`)
- [ ] 배포 완료 확인
- [ ] 프론트엔드 접근 가능
- [ ] API 연결 테스트

### 통합 테스트

- [ ] 프론트엔드에서 분석 시작 가능
- [ ] 백엔드에서 분석 처리 가능
- [ ] 분석 결과가 프론트엔드에 표시됨
- [ ] CORS 오류 없음
- [ ] 에러 핸들링 정상 작동

---

## 커스텀 도메인 설정

### Vercel 커스텀 도메인

1. Vercel 프로젝트 → Settings → Domains
2. 원하는 도메인 입력
3. DNS 설정 안내에 따라 도메인 설정
4. `ALLOWED_ORIGINS`에 커스텀 도메인 추가

### Railway 커스텀 도메인

1. Railway 프로젝트 → Settings → Domains
2. "Custom Domain" 추가
3. DNS 설정 안내에 따라 도메인 설정

---

## 모니터링 및 로그

### Railway 로그

- Railway 대시보드 → 프로젝트 → Deployments → 해당 배포 → Logs
- 실시간 로그 확인 가능

### Vercel 로그

- Vercel 대시보드 → 프로젝트 → Deployments → 해당 배포 → Logs
- 빌드 및 런타임 로그 확인 가능

---

## 업데이트 배포

### 자동 배포

- GitHub에 푸시하면 자동으로 배포됩니다
- Railway와 Vercel 모두 자동 배포 지원

### 수동 배포

- Railway: 대시보드에서 "Redeploy" 클릭
- Vercel: 대시보드에서 "Redeploy" 클릭

---

작성일: 2024년
최종 업데이트: 2024년
