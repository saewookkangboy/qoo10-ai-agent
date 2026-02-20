# Dev Agent Kit 통합 가이드

Qoo10 AI Agent 프로젝트에서 dev-agent-kit을 활용하는 방법을 안내합니다.

## 통합 목적

1. **문서 관리**: Spec-kit으로 PRD 및 기능 명세서 버전 관리
2. **작업 관리**: To-do 리스트로 개발 작업 추적
3. **프로젝트 관리**: Agent Roles로 역할 기반 개발
4. **백엔드 구축**: FastAPI로 RESTful API 서버 구축

## 설치 및 설정

### 1. Dev Agent Kit 경로 설정

```bash
# 환경 변수 설정 (선택사항)
export DEV_AGENT_KIT_PATH="/Users/chunghyo/dev-agent-kit"

# 또는 프로젝트 루트에 .env 파일 생성
echo "DEV_AGENT_KIT_PATH=/Users/chunghyo/dev-agent-kit" > .env
```

### 2. 프로젝트 초기화

```bash
# dev-agent-kit 디렉토리로 이동
cd /Users/chunghyo/dev-agent-kit

# 프로젝트 초기화 (qoo10-ai-agent용)
npm run init

# 또는 직접 스크립트 실행
node scripts/init-project.js
```

### 3. Spec-kit으로 문서 관리

#### PRD 문서 등록

```bash
cd /Users/chunghyo/dev-agent-kit

# PRD 문서를 Spec-kit에 등록
dev-agent spec create "Qoo10 AI Agent PRD" \
  --file /Users/chunghyo/Qoo10_AI_Agent_PRD.md \
  --type prd

# 기능 명세서 등록
dev-agent spec create "Qoo10 AI Agent 기능 명세서" \
  --file /Users/chunghyo/Qoo10_AI_Agent_기능명세서.md \
  --type spec
```

#### 문서 목록 조회

```bash
dev-agent spec list
```

#### 문서 검증

```bash
dev-agent spec validate
```

### 4. To-do 리스트 관리

#### Phase 1 작업 추가

```bash
# 핵심 기능 (P0)
dev-agent todo add "F1: URL 입력 및 분석 시작 기능 구현" \
  -p high -m "Phase 1"

dev-agent todo add "F2: 상품 상세페이지 분석 기능 구현" \
  -p high -m "Phase 1"

dev-agent todo add "F4: 매출 강화 아이디어 제안 기능 구현" \
  -p high -m "Phase 1"

dev-agent todo add "F6: 리포트 시각화 (카드 형태) 구현" \
  -p high -m "Phase 1"

# 백엔드 작업
dev-agent todo add "FastAPI 서버 구축" \
  -p high -m "Phase 1"

dev-agent todo add "크롤링 서비스 구현" \
  -p high -m "Phase 1"

dev-agent todo add "AI 분석 서비스 구현" \
  -p high -m "Phase 1"

# 프론트엔드 작업
dev-agent todo add "React 프로젝트 초기화" \
  -p high -m "Phase 1"

dev-agent todo add "URL 입력 컴포넌트 개발" \
  -p high -m "Phase 1"

dev-agent todo add "리포트 카드 컴포넌트 개발" \
  -p high -m "Phase 1"
```

#### 작업 목록 조회

```bash
# 전체 목록
dev-agent todo list

# Phase 1만 필터링
dev-agent todo list -m "Phase 1"

# 진행 중인 작업만
dev-agent todo list -s in-progress
```

#### 작업 완료 처리

```bash
dev-agent todo complete <id>
```

### 5. Agent Role 설정

#### 역할별 작업 분담

```bash
# 백엔드 개발자 역할
dev-agent role set --role backend

# 프론트엔드 개발자 역할
dev-agent role set --role frontend

# PM 역할
dev-agent role set --role pm
```

#### 역할별 To-do 필터링

```bash
# 현재 역할에 맞는 작업만 조회
dev-agent todo list --role
```

## 프로젝트 구조 통합

### Spec-kit 문서 위치

```
qoo10-ai-agent/
├── .spec-kit/                # dev-agent-kit이 생성
│   ├── prd/
│   │   └── qoo10-ai-agent-prd.md
│   └── specs/
│       └── qoo10-ai-agent-functional-spec.md
└── docs/                     # 로컬 문서 (선택사항)
    ├── PRD.md                # 원본 문서
    └── 기능명세서.md
```

### To-do 데이터 위치

```
qoo10-ai-agent/
└── .project-data/            # dev-agent-kit이 생성
    ├── todos.json            # To-do 리스트
    ├── role-config.json      # 역할 설정
    └── config.json           # 프로젝트 설정
```

## 개발 워크플로우

### 1. 프로젝트 시작

```bash
# 1. 역할 설정
dev-agent role set --role backend  # 또는 frontend, pm

# 2. 작업 목록 확인
dev-agent todo list

# 3. 작업 시작
dev-agent todo start <id>  # 작업 상태를 in-progress로 변경
```

### 2. 개발 중

```bash
# 작업 진행 상황 업데이트
dev-agent todo update <id> --note "진행 상황 메모"

# 작업 완료
dev-agent todo complete <id>
```

### 3. 문서 업데이트

```bash
# Spec-kit 문서 업데이트
dev-agent spec update "Qoo10 AI Agent PRD" \
  --file /Users/chunghyo/Qoo10_AI_Agent_PRD.md
```

## FastAPI 백엔드 통합

### API 서버 시작

```bash
cd /Users/chunghyo/dev-agent-kit
dev-agent api:start --port 8080
```

### API 엔드포인트

FastAPI 서버는 `http://localhost:8080`에서 실행되며, Swagger 문서는 `http://localhost:8080/docs`에서 확인할 수 있습니다.

## SEO 최적화 활용

### 웹사이트 분석 (향후)

```bash
# SEO 분석
dev-agent seo analyze https://qoo10-ai-agent.example.com

# AI SEO 최적화
dev-agent ai-seo optimize "콘텐츠" -k "qoo10" "ai" "커머스"
```

## 문제 해결

### Dev Agent Kit 명령어가 작동하지 않을 때

```bash
# 전역 설치 확인
cd /Users/chunghyo/dev-agent-kit
npm link

# 또는 직접 실행
node /Users/chunghyo/dev-agent-kit/bin/cli.js todo list
```

### Spec-kit 문서가 보이지 않을 때

```bash
# Spec-kit 초기화
cd /Users/chunghyo/dev-agent-kit
dev-agent spec init
```

### To-do 데이터가 저장되지 않을 때

```bash
# .project-data 디렉토리 확인
ls -la /Users/chunghyo/qoo10-ai-agent/.project-data

# 수동으로 생성
mkdir -p /Users/chunghyo/qoo10-ai-agent/.project-data
```

## 참고 자료

- [Dev Agent Kit README](../dev-agent-kit/README.ko.md)
- [통합 가이드](../dev-agent-kit/docs/INTEGRATION_GUIDE.md)
- [사용 가이드](../dev-agent-kit/docs/USAGE.md)
