# API 키 설정 및 AI 제공자(OpenAI/Gemini) 사용 방법

- **보안**: API 키는 환경 변수로만 관리. 코드·문서에 실제 키 금지. `.env`는 Git 제외. (dev-agent-kit 가이드라인 준수)
- **설정**: `api/.env.example`을 복사해 `api/.env` 생성 후 값 입력.

## 환경 변수

| 변수 | 용도 |
|------|------|
| `GEMINI_API_KEY` | Gemini (분석 강화, 채팅, 추천). 기본 우선. |
| `OPENAI_API_KEY` | OpenAI. Gemini 미설정 시 폴백. |
| `AI_PROVIDER` | `gemini`(기본) 또는 `openai` |
| `AI_MODEL_OPENAI` | 예: `gpt-4o-mini`, `gpt-4o` |
| `AI_MODEL_GEMINI` | 예: `gemini-2.5-flash`, `gemini-2.5-pro` |
| `AI_MAX_TOKENS` | (선택) 최대 출력 토큰 |

## 동작

- 기본: Gemini 사용 → 키 없으면 OpenAI 폴백.
- `AI_PROVIDER=openai`: OpenAI만 사용.

구현: `api/services/ai_provider.py`, `openai_service.py`, `gemini_service.py`, `chat_service.py`, `recommender.py`, `main.py`.
