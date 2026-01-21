# Gemini API 설정 가이드

## 환경 변수 설정

`.env` 파일에 다음을 추가하세요:

```bash
GEMINI_API_KEY=AIzaSyC6ZVqQ_rKLR7ijX2PicVJWeCIo8Eq0jd0
```

## 설정 확인

다음 명령어로 Gemini 서비스가 정상적으로 초기화되는지 확인할 수 있습니다:

```bash
cd api
python -c "from services.gemini_service import GeminiService; g = GeminiService(); print('Gemini 초기화:', '성공' if g.model else '실패 (API 키 확인 필요)')"
```

## 사용 위치

Gemini API는 다음 위치에서 자동으로 사용됩니다:

1. **분석 강화**: `main.py`의 `perform_analysis`에서 자동으로 Gemini를 사용하여 분석 강화
2. **추천 생성**: `recommender.py`에서 Gemini를 우선적으로 사용하여 AI 추천 생성
3. **챗봇 응답**: `chat_service.py`에서 Gemini를 우선적으로 사용하여 응답 생성

## 우선순위

- **추천 생성**: Gemini AI 추천 → 메뉴얼 기반 추천
- **챗봇**: Gemini → OpenAI → 기본 응답
- **분석**: 기본 분석 → Gemini AI 강화

## 주의사항

1. API 키는 `.env` 파일에 저장하고 Git에 커밋하지 마세요
2. API 키가 없어도 시스템은 정상 작동합니다 (Gemini 기능만 비활성화)
3. Gemini 실패 시 자동으로 폴백됩니다
