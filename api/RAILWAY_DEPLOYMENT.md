# Railway 배포 가이드

이 문서는 Qoo10 AI Agent 백엔드를 Railway에 배포하는 방법을 설명합니다.

## 1. Railway 프로젝트 생성

### 1.1 Railway 계정 준비
1. [Railway](https://railway.app)에 로그인 또는 회원가입
2. GitHub 계정으로 연동 (권장)

### 1.2 프로젝트 연결
1. Railway 대시보드에서 "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. GitHub 저장소 선택
4. 프로젝트 설정:
   - **Root Directory**: `api`
   - **Build Command**: 자동 감지 (railway.json 사용)
   - **Start Command**: 자동 감지 (railway.json 사용)

## 2. 환경 변수 설정

Railway 대시보드 → 프로젝트 → Variables 탭에서 환경 변수를 설정합니다.

### 필수 환경 변수

```bash
# 데이터베이스 연결 URL
DATABASE_URL=postgresql://user:password@host:port/database
```

### 선택적 환경 변수

```bash
# CORS 허용 오리진 (프론트엔드 URL)
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app

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

## 3. PostgreSQL 데이터베이스 추가 (권장)

1. Railway 프로젝트 → "New" → "Database" → "Add PostgreSQL"
2. 생성된 데이터베이스의 `DATABASE_URL`을 복사
3. 환경 변수에 `DATABASE_URL` 설정

> **참고**: SQLite도 사용 가능하지만, 프로덕션에서는 PostgreSQL을 권장합니다.

## 4. 배포 확인

1. Railway 대시보드 → Deployments 탭에서 배포 상태 확인
2. 배포 완료 후 생성된 URL 확인 (예: `https://your-app-name.railway.app`)
3. 헬스 체크: `https://your-app-name.railway.app/health`
4. API 문서: `https://your-app-name.railway.app/docs`

## 5. CORS 설정

프론트엔드 URL을 `ALLOWED_ORIGINS`에 추가:

```bash
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,https://your-custom-domain.com
```

## 6. 문제 해결

### 빌드 실패
- Railway 로그 확인: Deployments → 해당 배포 → Logs
- `requirements.txt` 확인
- Python 버전 확인 (`runtime.txt`)

### Playwright 설치 실패
- `railway.json`의 `buildCommand`에 `playwright install chromium` 포함 확인

### 서버 시작 실패
- 포트 설정 확인 (Railway는 자동으로 `$PORT` 설정)
- 환경 변수 확인

### CORS 오류
- `ALLOWED_ORIGINS` 환경 변수에 프론트엔드 URL 추가

## 참고 자료

- [Railway 문서](https://docs.railway.app)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
