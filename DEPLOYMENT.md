# 배포 가이드

이 문서는 Qoo10 AI Agent 프로젝트를 Vercel(프론트엔드)과 Railway(백엔드)에 배포하는 방법을 설명합니다.

## 배포 아키텍처

- **프론트엔드**: Vercel
- **백엔드 API**: Railway
- **데이터베이스**: PostgreSQL (Railway 제공)

## 사전 준비

1. GitHub 저장소 준비
2. Vercel 계정 생성
3. Railway 계정 생성
4. OpenAI 및 Anthropic API 키 준비

---

## 1. 프론트엔드 배포 (Vercel)

### 1.1 Vercel 프로젝트 생성

1. [Vercel](https://vercel.com)에 로그인
2. "Add New Project" 클릭
3. GitHub 저장소 선택
4. 프로젝트 설정:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

### 1.2 환경 변수 설정

Vercel 대시보드에서 환경 변수 추가:

```
VITE_API_URL=https://your-railway-backend-url.railway.app
```

> **참고**: Railway 백엔드 URL은 Railway 배포 후에 설정합니다.

### 1.3 배포

- Vercel은 자동으로 GitHub에 푸시할 때마다 배포합니다
- 또는 Vercel 대시보드에서 "Deploy" 버튼 클릭

---

## 2. 백엔드 배포 (Railway)

### 2.1 Railway 프로젝트 생성

1. [Railway](https://railway.app)에 로그인
2. "New Project" 클릭
3. "Deploy from GitHub repo" 선택
4. 저장소 선택 후 `api` 디렉토리 선택

### 2.2 PostgreSQL 데이터베이스 추가

1. Railway 프로젝트에서 "New" 버튼 클릭
2. "Database" → "Add PostgreSQL" 선택
3. PostgreSQL 서비스가 생성되면 자동으로 `DATABASE_URL` 환경 변수가 설정됩니다

### 2.3 환경 변수 설정

Railway 프로젝트의 "Variables" 탭에서 다음 환경 변수 추가:

```bash
# OpenAI API 키
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API 키
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# CORS 설정 (Vercel 프론트엔드 URL)
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app

# 포트는 Railway가 자동으로 설정 (PORT 환경 변수)
```

> **참고**: `DATABASE_URL`은 PostgreSQL 서비스를 추가하면 자동으로 설정됩니다.

### 2.4 배포 설정 확인

Railway는 다음 파일들을 자동으로 인식합니다:

- `Procfile`: 서버 시작 명령어
- `requirements.txt`: Python 패키지 의존성
- `runtime.txt`: Python 버전

### 2.5 커스텀 도메인 설정 (선택사항)

1. Railway 프로젝트 → "Settings" → "Networking"
2. "Generate Domain" 클릭하여 Railway 도메인 생성
3. 또는 "Custom Domain"에서 도메인 추가

---

## 3. 프론트엔드와 백엔드 연결

### 3.1 백엔드 URL 확인

Railway 배포 후 생성된 URL 확인:
- Railway 프로젝트 → "Settings" → "Networking" → "Public Domain"

### 3.2 프론트엔드 환경 변수 업데이트

Vercel 대시보드에서 `VITE_API_URL` 환경 변수를 Railway 백엔드 URL로 업데이트:

```
VITE_API_URL=https://your-railway-backend-url.railway.app
```

### 3.3 재배포

환경 변수 변경 후 Vercel에서 자동으로 재배포되거나, 수동으로 재배포할 수 있습니다.

---

## 4. CORS 설정 확인

백엔드 `main.py`에서 CORS 설정이 올바른지 확인:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

프로덕션에서는 `allow_origins`를 Vercel 프론트엔드 URL로 제한하는 것이 좋습니다:

```python
allow_origins=[
    "https://your-vercel-app.vercel.app",
    "https://your-custom-domain.com"
]
```

---

## 5. 데이터베이스 마이그레이션

PostgreSQL 데이터베이스는 애플리케이션 시작 시 자동으로 테이블이 생성됩니다.

`database.py`의 `_init_database()` 메서드가 실행되면서 필요한 테이블들이 생성됩니다.

---

## 6. 배포 확인

### 6.1 백엔드 확인

```bash
# Health check
curl https://your-railway-backend-url.railway.app/docs

# API 테스트
curl https://your-railway-backend-url.railway.app/api/v1/analyze \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=..."}'
```

### 6.2 프론트엔드 확인

브라우저에서 Vercel 배포 URL 접속하여 정상 작동 확인

---

## 7. 문제 해결

### 7.1 백엔드 연결 오류

- Railway 로그 확인: Railway 프로젝트 → "Deployments" → 로그 확인
- 환경 변수 확인: `DATABASE_URL`, `OPENAI_API_KEY` 등이 올바르게 설정되었는지 확인
- 포트 확인: Railway는 `PORT` 환경 변수를 자동으로 설정하므로 `Procfile`에서 `$PORT` 사용

### 7.2 프론트엔드 API 호출 오류

- CORS 오류: 백엔드 CORS 설정 확인
- 404 오류: `VITE_API_URL` 환경 변수가 올바른지 확인
- 네트워크 오류: Railway 백엔드가 정상적으로 실행 중인지 확인

### 7.3 데이터베이스 연결 오류

- `DATABASE_URL` 환경 변수 확인
- Railway PostgreSQL 서비스가 정상적으로 실행 중인지 확인
- 로그에서 데이터베이스 연결 오류 메시지 확인

---

## 8. 지속적 배포 (CI/CD)

### 8.1 Vercel

- GitHub에 푸시하면 자동으로 배포됩니다
- Pull Request마다 Preview 배포가 생성됩니다

### 8.2 Railway

- GitHub에 푸시하면 자동으로 배포됩니다
- `api` 디렉토리의 변경사항만 감지하여 배포합니다

---

## 9. 모니터링

### 9.1 Vercel

- Vercel 대시보드에서 배포 상태, 트래픽, 에러 로그 확인

### 9.2 Railway

- Railway 대시보드에서 배포 상태, 로그, 메트릭 확인
- PostgreSQL 데이터베이스 메트릭도 확인 가능

---

## 10. 비용 최적화

### 10.1 Vercel

- Hobby 플랜: 무료 (개인 프로젝트용)
- Pro 플랜: 팀 협업 및 고급 기능

### 10.2 Railway

- Hobby 플랜: $5/월 (제한된 리소스)
- Pro 플랜: 사용량 기반 과금

---

## 참고 자료

- [Vercel 문서](https://vercel.com/docs)
- [Railway 문서](https://docs.railway.app)
- [PostgreSQL 문서](https://www.postgresql.org/docs/)
