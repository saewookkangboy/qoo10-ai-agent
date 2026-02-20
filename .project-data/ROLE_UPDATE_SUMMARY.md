# 역할별 업데이트 대상 요약 (Agent Role 시스템)

**프로젝트**: qoo10-ai-agent  
**기준**: dev-agent-kit Agent Role  
**갱신일**: 2026-02-20  

---

## 1. 역할별 업데이트 대상 항목 요약

| 역할 | 지금 업데이트할 작업 (요약) | 우선순위·마일스톤 |
|------|----------------------------|-------------------|
| **PM** | 테스트·배포 일정 조율, phase-checklist 진행률 점검 | Phase 1, medium |
| **Frontend Developer** | React 초기화 → URL 입력 → 리포트 시각화/카드 컴포넌트 | Phase 1, high |
| **Backend Developer** | FastAPI → 크롤링 → AI 분석 → F1/F2/F4 순차 구현, Phase 2 확장 기능 | Phase 1·2, high/medium |
| **Server/DB Developer** | DB 설계·구축, 배포 환경(Docker·CI/CD) | Phase 1, high/medium |
| **Security Manager** | 전용 todo 없음 — 보안 체크리스트·API 인증 요구사항 문서화 권장 | Phase 1 중반 이후 |
| **UI/UX Designer** | 리포트 카드·URL 입력·리포트 카드 컴포넌트 UX/레이아웃 스펙 | Phase 1, high |
| **AI Marketing Researcher** | F4 매출 강화 로직·메뉴얼 지식베이스, Phase 2 Shop/경쟁사 분석 요구사항 | Phase 1·2, high/medium |

---

## 2. 생성·수정한 파일 경로

- `.project-data/role-config.json` — 역할 정의, category 매핑, 가이드라인·next_steps
- `.project-data/role-actions.json` — 역할별 todo_id 목록(우선순위·마일스톤 반영)
- `.project-data/ROLE_UPDATE_SUMMARY.md` — 본 요약 문서

---

## 3. 다음에 실행할 명령어·후속 작업 제안

- **역할 설정**: `dev-agent role set --role [pm|frontend_developer|backend_developer|server_db_developer|security_manager|ui_ux_designer|ai_marketing_researcher]`  
  (실제 CLI가 있다면 위 id 사용)
- **Todo 조회**: 역할별 할 일은 `role-actions.json`의 `role_actions.[역할_id]` 참고
- **Phase 점검**: `phase-checklist.json`과 `todos.json` 마일스톤 동기화 후 PM이 진행률 리뷰
- **보안**: Security Manager — `.spec-kit`에 API 인증/인가 요구사항 문서 추가 권장
- **의존성 순서**: Backend는 todo_005 → todo_006 → todo_007 → todo_001 → todo_002 → todo_003 순 권장

---

*세부 todo 설명은 `todos.json`, 역할별 상세 가이드는 `role-config.json` 참고.*
