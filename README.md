# Qoo10 Sales Intelligence Agent

Qoo10 Japan 입점 한국 브랜드를 위한 AI 기반 커머스 분석 및 매출 강화 플랫폼

## 프로젝트 개요

Qoo10 Japan 입점 브랜드의 URL을 입력하면, AI가 상품/샵을 분석하고 메뉴얼 기반의 실전적인 매출 강화 아이디어를 제안하는 커머스 분석 AI 에이전트입니다.

## Dev Agent Kit 통합

이 프로젝트는 [dev-agent-kit](https://github.com/saewookkangboy/dev-agent-kit)을 활용하여 개발됩니다.

### 주요 활용 기능

1. **Spec-kit**: PRD 및 기능 명세서 관리
2. **To-do 관리**: 개발 작업 추적
3. **FastAPI 백엔드**: RESTful API 서버
4. **SEO 최적화**: 웹 최적화 기능
5. **AI 강화학습 (Agent Lightning 연동)**: 분석 결과 trajectory 수집 및 `learning_trajectory` 저장 — [doc/agents/AI-Reinforcement-Learning.md](doc/agents/AI-Reinforcement-Learning.md)

## 에이전트 오케스트레이션

전체 서비스는 **Orchestration 중심**으로 구조화되어 있습니다. 분석(크롤링·영역 추출)·리포트·개선 제안·점수 출력이 단계별 에이전트로 나뉘어 데이터 파이프라인이 명확히 흐르도록 설계되어 있습니다.

- **설계 개요·데이터 파이프라인**: [doc/agents/README.md](doc/agents/README.md)
- **Orchestration Agent**: [doc/agents/Orchestration-Agent.md](doc/agents/Orchestration-Agent.md)
- **기능별 Agent**: Crawl, Analysis, Recommendation, Checklist, Validation, Report & Output — [doc/agents/](doc/agents/) 내 각 `*-Agent.md` 참고

## 프로젝트 구조

```
qoo10-ai-agent/
├── doc/                       # 프로젝트 문서
│   ├── agents/               # 에이전트 오케스트레이션 설계
│   │   ├── README.md         # 파이프라인 개요·에이전트 역할 매핑
│   │   ├── Orchestration-Agent.md
│   │   ├── Crawl-Agent.md
│   │   ├── Analysis-Agent.md
│   │   └── ... (Recommendation, Checklist, Validation, Report-Output)
│   ├── archive/              # 서비스 비필수 문서 (PRD, 명세, 테스트·진단 리포트 등)
│   └── ...
├── api/                      # FastAPI 백엔드
│   ├── main.py               # FastAPI 애플리케이션
│   ├── routes/               # API 라우트
│   ├── services/             # 비즈니스 로직
│   └── models/               # 데이터 모델
├── frontend/                 # 프론트엔드 (React)
│   ├── src/
│   │   ├── components/       # React 컴포넌트
│   │   ├── pages/            # 페이지
│   │   └── utils/            # 유틸리티
│   └── public/
├── .spec-kit/                # Spec-kit 문서 (dev-agent-kit)
├── .project-data/            # 프로젝트 데이터 (dev-agent-kit)
│   ├── todos.json            # To-do 리스트
│   └── config.json           # 프로젝트 설정
└── package.json
```



## 설치 및 설정

### 1. Dev Agent Kit 설치

```bash
# dev-agent-kit 클론 (이미 완료)
cd /Users/chunghyo/dev-agent-kit
npm install
npm run setup
```

### 2. 프로젝트 초기화

```bash
cd /Users/chunghyo/qoo10-ai-agent

# dev-agent-kit을 사용하여 프로젝트 초기화
cd /Users/chunghyo/dev-agent-kit
npm run init

# 또는 직접 초기화
node /Users/chunghyo/dev-agent-kit/scripts/init-project.js
```

### 3. Spec-kit으로 문서 관리

```bash
# PRD 문서 생성
cd /Users/chunghyo/dev-agent-kit
dev-agent spec create "Qoo10 AI Agent PRD"

# 기능 명세서 생성
dev-agent spec create "Qoo10 AI Agent 기능 명세서"
```

### 4. To-do 리스트 관리

```bash
# 개발 작업 추가
dev-agent todo add "URL 입력 기능 구현" -p high -m "Phase 1"
dev-agent todo add "상품 페이지 분석 기능" -p high -m "Phase 1"
dev-agent todo add "리포트 시각화" -p medium -m "Phase 1"

# 작업 목록 확인
dev-agent todo list
```

### 5. API 키 설정 및 AI 제공자(OpenAI/Gemini) 사용 방법

- **보안**: API 키는 **환경 변수로만** 설정합니다. 코드나 `.env` 파일을 Git에 커밋하지 마세요. (dev-agent-kit API 키 관리 가이드라인 준수)
- **설정 위치**: `api/` 디렉터리에서 `cp .env.example .env` 후 `.env`에 실제 키 값을 입력합니다.

| 환경 변수 | 용도 |
|-----------|------|
| `GEMINI_API_KEY` | Google Gemini (분석 강화, 채팅, 추천). 기본 우선 사용. |
| `OPENAI_API_KEY` | OpenAI (분석 강화, 채팅, 추천). Gemini 미설정 시 폴백. |
| `AI_PROVIDER` | `gemini`(기본) 또는 `openai`. `openai`면 OpenAI만 사용. |
| `AI_MODEL_OPENAI` | OpenAI 모델 (예: `gpt-4o-mini`, `gpt-4o`). 비용/성능 조절. |
| `AI_MODEL_GEMINI` | Gemini 모델 (예: `gemini-2.5-flash`, `gemini-2.5-pro`). |
| `AI_MAX_TOKENS` | (선택) AI 응답 최대 토큰 수. |

동작 요약: **Gemini 우선** → 키가 없으면 **OpenAI 폴백**. `AI_PROVIDER=openai`로 두면 OpenAI만 사용합니다.

## 개발 워크플로우

### Phase 1: MVP 개발 (3개월)

1. **URL 입력 및 분석 시작** (F1)
   ```bash
   dev-agent todo add "URL 입력 기능 구현" -p high -m "Phase 1"
   dev-agent todo add "URL 검증 로직 구현" -p high -m "Phase 1"
   ```

2. **상품 상세페이지 분석** (F2)
   ```bash
   dev-agent todo add "크롤링 서비스 구현" -p high -m "Phase 1"
   dev-agent todo add "이미지 분석 로직" -p high -m "Phase 1"
   dev-agent todo add "SEO 분석 로직" -p high -m "Phase 1"
   ```

3. **매출 강화 아이디어 제안** (F4)
   ```bash
   dev-agent todo add "메뉴얼 지식베이스 구축" -p high -m "Phase 1"
   dev-agent todo add "AI 제안 생성 로직" -p high -m "Phase 1"
   ```

4. **리포트 시각화** (F6)
   ```bash
   dev-agent todo add "카드 컴포넌트 개발" -p high -m "Phase 1"
   dev-agent todo add "대시보드 레이아웃" -p high -m "Phase 1"
   ```

## 기술 스택

### 백엔드
- **FastAPI**: Python 기반 RESTful API
- **Web Scraping**: Qoo10 페이지 크롤링
- **AI/ML**: 자연어 처리, 이미지 분석

### 프론트엔드
- **React**: UI 프레임워크
- **TypeScript**: 타입 안정성
- **Tailwind CSS**: 스타일링

### 개발 도구
- **Dev Agent Kit**: 프로젝트 관리
- **Spec-kit**: 문서 관리
- **Vitest**: 테스트 프레임워크

## API 엔드포인트

### 분석 시작
```
POST /api/v1/analyze
Body: { "url": "string" }
Response: { "analysis_id": "string", "status": "processing" }
```

### 분석 결과 조회
```
GET /api/v1/analyze/{analysis_id}
Response: AnalysisResult
```

### 리포트 다운로드
```
GET /api/v1/analyze/{analysis_id}/download?format=pdf|excel
Response: File
```

## 배포

프로젝트 배포 가이드는 [DEPLOYMENT.md](./DEPLOYMENT.md)를 참조하세요.

### 배포 플랫폼

- **프론트엔드**: Vercel (React + Vite)
- **백엔드**: Railway (FastAPI + Python)
- **데이터베이스**: PostgreSQL (Railway)

### 빠른 시작

1. **Railway 백엔드 배포**
   - [Railway 배포 가이드](./api/RAILWAY_DEPLOYMENT.md) 참조
   - GitHub 저장소 연결 → Root Directory: `api`
   - 환경 변수 설정 (`DATABASE_URL`, `ALLOWED_ORIGINS`)

2. **Vercel 프론트엔드 배포**
   - [Vercel 배포 가이드](./frontend/VERCEL_DEPLOYMENT.md) 참조
   - GitHub 저장소 연결 → Root Directory: `frontend`
   - 환경 변수 설정 (`VITE_API_URL`)

3. **배포 확인**
   - Railway: `https://your-app.railway.app/health`
   - Vercel: 배포된 URL 접속하여 기능 테스트

## 참고 문서

- [PRD 문서](./docs/PRD.md)
- [기능 명세서](./docs/기능명세서.md)
- [배포 가이드](./DEPLOYMENT.md)
- [Qoo10 큐텐 대학 메뉴얼](../Qoo10_큐텐대학_한국어_메뉴얼.md)

## 라이선스

MIT License

## 작성자

Park chunghyo
