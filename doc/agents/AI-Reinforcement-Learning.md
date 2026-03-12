# AI 강화학습 연동 (dev-agent-kit / Agent Lightning)

**목적**: 분석 결과를 저장하고, 강화학습(RL) 및 프롬프트 최적화에 활용할 수 있는 **trajectory 데이터**를 수집합니다. `.cursor/agents/dev-agent-kit.md`의 "AI 강화학습 (Agent Lightning)" 영역과 연동됩니다.

---

## 1. 리서치 요약: Microsoft Agent Lightning

- **출처**: [Agent Lightning - Microsoft Research](https://www.microsoft.com/en-us/research/project/agent-lightning/), [GitHub](https://github.com/microsoft/agent-lightning), [문서](https://microsoft.github.io/agent-lightning/latest/)
- **특징**:
  - **거의 제로 코드 변경**으로 기존 AI 에이전트에 RL을 추가
  - **프레임워크 무관**: LangChain, OpenAI Agent SDK, AutoGen, CrewAI, 단순 Python OpenAI 등 모두 지원
  - **Lightning Client**: 에이전트 실행 + trajectory 자동 수집
  - **Lightning Server**: GPU 서버에서 RL 학습, OpenAI 호환 API 노출
  - **통일 데이터 인터페이스**: 에이전트 경험을 MDP(상태·행동·보상) 형식으로 변환
  - **알고리즘**: PPO, GRPO, APO(Automatic Prompt Optimization), SFT 등

우리 프로젝트에서는 **분석 파이프라인 1회 실행 = 1 trajectory**로 간주하고, state/action/reward를 DB에 저장해 두면, 이후 Agent Lightning 또는 다른 RL 파이프라인에서 학습 데이터로 사용할 수 있습니다.

---

## 2. 본 프로젝트 반영 사항

### 2.1 분석 결과 저장

- **기존**: `HistoryManager.save_analysis_history()`로 `analysis_history` 테이블에 분석 결과 저장.
- **추가**: 완료 시 **trajectory**를 `learning_trajectory` 테이블에 저장하여 RL용 데이터로 활용.

### 2.2 학습 데이터 스키마 (`learning_trajectory`)

이 테이블은 **별도 마이그레이션 스크립트 없이** `api/services/database.py`의 `CrawlerDatabase._init_database()`에서 `CREATE TABLE IF NOT EXISTS`로 앱 기동 시 자동 생성됩니다. (Alembic 등 마이그레이션 툴은 사용하지 않음.)

| 컬럼 | 설명 |
|------|------|
| `analysis_id` | 분석 ID (UNIQUE) |
| `url` | 분석한 URL |
| `url_type` | product / shop |
| `state_snapshot` | 상태 요약 (크롤링·검증 결과 등) — JSON |
| `actions_snapshot` | 행동 요약 (AI 점수·추천·체크리스트 등) — JSON |
| `reward` | 보상 (기본: overall_score) |
| `metadata_json` | 메타데이터 (url_type, recommendations_count 등) |
| `created_at` | 생성 시각 |

- **state**: 분석 입력/컨텍스트 요약 (상품·샵·검증 요약).
- **actions**: AI가 수행한 판단·추천 요약 (점수, 추천 목록, 체크리스트 요약).
- **reward**: `overall_score` 또는 향후 사용자 피드백으로 확장 가능.

### 2.3 서비스

- **파일**: `api/services/learning_data_service.py`
- **클래스**: `LearningDataService.save_trajectory(analysis_id, url, url_type, analysis_result, reward=None)`
- **호출 시점**: `_save_history_and_notify_async()` 내부 — 히스토리 저장 직후, 알림 전에 호출.
- **환경 변수**: `ENABLE_LEARNING_TRAJECTORY` — 1 = enabled, 0 = disabled (기본값 1).

### 2.4 데이터 흐름

```
[분석 완료]
    → history_manager.save_analysis_history()  # 기존
    → learning_data_service.save_trajectory() # state/actions/reward 저장
    → notification_service.notify_*()
```

---

## 3. Agent Lightning 연동 시 참고

- **데이터 내보내기**: `learning_trajectory` 테이블을 MDP 형식으로 익스포트하면 Lightning Server 또는 다른 RL 툴에서 사용 가능.
- **보상 설계**: 현재는 `overall_score`를 reward로 사용. 사용자 피드백(좋아요/개선 적용 여부)을 추가 컬럼이나 별도 테이블로 저장하면 reward 신호를 강화할 수 있음.
- **실제 RL 학습**: GPU 환경에서 Agent Lightning 서버를 띄우고, 수집된 trajectory로 PPO/GRPO 등 학습을 돌리는 것은 별도 인프라 및 스크립트가 필요합니다. 본 문서는 **데이터 수집 및 스키마**까지를 범위로 합니다.

---

## 4. 관련 파일

- `api/services/learning_data_service.py` — trajectory 저장 로직
- `api/services/database.py` — `learning_trajectory` 테이블 정의 (Postgres / SQLite)
- `api/main.py` — `_save_history_and_notify_async()` 내 `learning_data_service.save_trajectory()` 호출
- `api/.env.example` — `ENABLE_LEARNING_TRAJECTORY` 설명
