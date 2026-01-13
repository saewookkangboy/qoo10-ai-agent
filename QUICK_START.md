# Qoo10 AI Agent - 빠른 시작 가이드

## Dev Agent Kit 활용하기

### 1. 초기 설정 완료 확인

프로젝트가 이미 초기화되어 있습니다:
- ✅ 프로젝트 구조 생성
- ✅ To-do 리스트 생성 (10개 작업)
- ✅ 프로젝트 설정 파일 생성
- ✅ 문서 복사 완료

### 2. Dev Agent Kit 사용하기

#### To-do 리스트 확인

```bash
# dev-agent-kit 디렉토리로 이동
cd /Users/chunghyo/dev-agent-kit

# To-do 리스트 확인 (qoo10-ai-agent 프로젝트)
# 주의: dev-agent-kit은 현재 프로젝트 디렉토리 기준으로 작동합니다
cd /Users/chunghyo/qoo10-ai-agent
# 또는 직접 JSON 파일 확인
cat .project-data/todos.json
```

#### 작업 상태 업데이트

To-do 리스트는 `/Users/chunghyo/qoo10-ai-agent/.project-data/todos.json`에 저장되어 있습니다.

수동으로 업데이트하거나, 향후 dev-agent-kit CLI를 통해 관리할 수 있습니다.

### 3. 프로젝트 구조

```
qoo10-ai-agent/
├── docs/                      # 문서
│   ├── PRD.md                # 제품 요구사항 문서
│   └── 기능명세서.md         # 기능 명세서
├── api/                      # FastAPI 백엔드 (향후)
├── frontend/                 # React 프론트엔드 (향후)
├── .project-data/           # 프로젝트 데이터
│   ├── todos.json           # To-do 리스트
│   └── config.json          # 프로젝트 설정
├── README.md
├── DEV_AGENT_KIT_INTEGRATION.md
└── package.json
```

### 4. 다음 단계

#### Phase 1 개발 시작

1. **FastAPI 백엔드 구축**
   ```bash
   cd api
   # FastAPI 프로젝트 초기화
   ```

2. **React 프론트엔드 구축**
   ```bash
   cd frontend
   # React 프로젝트 초기화
   npx create-react-app . --template typescript
   ```

3. **크롤링 서비스 개발**
   - Qoo10 페이지 크롤링 로직
   - 데이터 파싱 및 저장

4. **AI 분석 서비스 개발**
   - 이미지 분석
   - 텍스트 분석 (SEO, 설명)
   - 가격 분석
   - 리뷰 분석

### 5. Dev Agent Kit 명령어 참고

```bash
# dev-agent-kit 디렉토리에서 실행
cd /Users/chunghyo/dev-agent-kit

# To-do 추가
dev-agent todo add "작업 내용" -p high -m "Phase 1"

# To-do 목록
dev-agent todo list

# To-do 완료
dev-agent todo complete <id>

# Spec-kit 문서 생성
dev-agent spec create "문서명"

# 역할 설정
dev-agent role set --role backend
```

## 참고 문서

- [README.md](./README.md) - 프로젝트 개요
- [DEV_AGENT_KIT_INTEGRATION.md](./DEV_AGENT_KIT_INTEGRATION.md) - 통합 가이드
- [docs/PRD.md](./docs/PRD.md) - 제품 요구사항
- [docs/기능명세서.md](./docs/기능명세서.md) - 기능 명세서
