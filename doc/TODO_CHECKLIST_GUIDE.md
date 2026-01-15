# Todo & Checklist 가이드

Qoo10 AI Agent 프로젝트의 Todo 리스트와 Checklist 관리 가이드입니다.

## 파일 구조

```
.project-data/
├── todos.json              # 개발 작업 Todo 리스트
├── checklists.json         # 메뉴얼 기반 체크리스트
└── phase-checklist.json    # Phase별 완료 체크리스트
```

## Todo 리스트

### 파일 위치
`/Users/chunghyo/qoo10-ai-agent/.project-data/todos.json`

### 구조
- **17개 작업**이 Phase별로 정리되어 있습니다
- 각 작업은 다음 정보를 포함합니다:
  - `id`: 고유 식별자
  - `description`: 작업 설명
  - `priority`: 우선순위 (high, medium, low)
  - `status`: 상태 (pending, in-progress, completed)
  - `milestone`: 마일스톤 (Phase 1, Phase 2, Phase 3)
  - `category`: 카테고리 (backend, frontend, testing, devops)
  - `dependencies`: 의존성 작업 ID 목록
  - `subtasks`: 세부 작업 목록

### Phase별 작업 분류

#### Phase 1 (MVP - 3개월)
- **10개 핵심 작업**
  - F1: URL 입력 및 분석 시작
  - F2: 상품 상세페이지 분석
  - F4: 매출 강화 아이디어 제안
  - F6: 리포트 시각화
  - FastAPI 서버 구축
  - 크롤링 서비스
  - AI 분석 서비스
  - React 프로젝트 초기화
  - URL 입력 컴포넌트
  - 리포트 카드 컴포넌트

#### Phase 2 (4-6개월)
- **4개 확장 작업**
  - F3: Shop 카테고리 분석
  - F5: 메뉴얼 기반 체크리스트
  - F7: 경쟁사 비교 분석
  - F8: 리포트 다운로드

#### Phase 3 (7-9개월)
- **3개 고급 작업**
  - F9: 히스토리 관리
  - F10: 알림 기능
  - F11: 배치 분석

### 사용 방법

#### Todo 확인
```bash
# JSON 파일 직접 확인
cat .project-data/todos.json

# 또는 dev-agent-kit 사용 (향후)
cd /Users/chunghyo/dev-agent-kit
dev-agent todo list
```

#### Todo 상태 업데이트
JSON 파일을 직접 수정하거나, 향후 dev-agent-kit CLI를 통해 관리할 수 있습니다.

```json
{
  "id": "todo_001",
  "status": "in-progress",  // pending → in-progress → completed
  ...
}
```

## Checklist

### 파일 위치
`/Users/chunghyo/qoo10-ai-agent/.project-data/checklists.json`

### 구조
- **5개 카테고리**의 체크리스트가 포함되어 있습니다:
  1. **판매 준비 체크리스트** (6개 항목)
  2. **매출 증대 체크리스트** (10개 항목 - 큐텐 대학 메뉴얼 기반)
  3. **광고/프로모션 체크리스트** (8개 항목)
  4. **상품 페이지 완성도 체크리스트** (6개 항목)
  5. **Shop 레벨 향상 체크리스트** (3개 항목)

### 각 체크리스트 항목 구조
- `id`: 고유 식별자
- `title`: 항목 제목
- `description`: 상세 설명
- `status`: 상태 (pending, completed)
- `auto_checkable`: 자동 체크 가능 여부
- `manual_check`: 수동 체크 필요 여부

### 자동 체크 vs 수동 체크

#### 자동 체크 가능 항목
- 상품 정보 존재 여부
- 이미지 개수, 품질
- 검색어 설정 여부
- 가격 정보
- 광고 설정 여부

#### 수동 체크 필요 항목
- 고객 서비스 품질
- 지속적인 개선 활동
- Shop 레벨 향상 목표 달성

### 사용 방법

#### Checklist 확인
```bash
cat .project-data/checklists.json
```

#### Checklist 완성도 계산
```javascript
// 예시: 판매 준비 체크리스트 완성도
const completed = items.filter(item => item.status === 'completed').length;
const total = items.length;
const completionRate = (completed / total) * 100;
```

## Phase Checklist

### 파일 위치
`/Users/chunghyo/qoo10-ai-agent/.project-data/phase-checklist.json`

### 구조
각 Phase별로 완료해야 할 주요 마일스톤이 정리되어 있습니다.

### Phase 1 체크리스트
- ✅ 프로젝트 초기화 완료
- ⬜ FastAPI 서버 구축 완료
- ⬜ 크롤링 서비스 구현 완료
- ⬜ AI 분석 서비스 구현 완료
- ⬜ React 프론트엔드 구축 완료
- ⬜ F1: URL 입력 기능 완료
- ⬜ F2: 상품 상세페이지 분석 완료
- ⬜ F4: 매출 강화 아이디어 제안 완료
- ⬜ F6: 리포트 시각화 완료
- ⬜ 통합 테스트 완료
- ⬜ 배포 환경 설정 완료

## 통합 활용

### 개발 워크플로우

1. **Todo 리스트에서 작업 선택**
   ```bash
   # Phase 1 작업 확인
   cat .project-data/todos.json | jq '.todos[] | select(.milestone == "Phase 1")'
   ```

2. **작업 시작**
   - Todo 상태를 `pending` → `in-progress`로 변경
   - 작업 진행

3. **작업 완료**
   - Todo 상태를 `in-progress` → `completed`로 변경
   - Phase Checklist 업데이트

4. **Checklist 확인**
   - 상품/샵 분석 시 자동으로 Checklist 평가
   - 수동 체크 항목은 사용자가 직접 확인

### 예시: 상품 분석 시 Checklist 자동 평가

```python
# 의사코드
def evaluate_checklist(product_data):
    checklist = load_checklist()
    
    for item in checklist.items:
        if item.auto_checkable:
            if item.id == "item_001":  # 상품 등록 완료
                item.status = "completed" if product_data.name else "pending"
            elif item.id == "item_025":  # 썸네일 품질
                item.status = "completed" if product_data.thumbnail_quality >= 800 else "pending"
            # ... 기타 자동 체크 항목
    
    return calculate_completion_rate(checklist)
```

## 업데이트 방법

### 수동 업데이트
JSON 파일을 직접 편집하여 상태를 업데이트할 수 있습니다.

### 자동 업데이트 (향후)
개발이 진행되면 API나 CLI를 통해 자동으로 업데이트할 수 있습니다.

## 참고 자료

- [PRD 문서](./docs/PRD.md) - 제품 요구사항
- [기능 명세서](./docs/기능명세서.md) - 상세 기능 명세
- [Qoo10 큐텐 대학 메뉴얼](../Qoo10_큐텐대학_한국어_메뉴얼.md) - 메뉴얼 기반 체크리스트 출처
