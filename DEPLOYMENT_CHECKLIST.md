# 배포 체크리스트

배포 전에 다음 항목들을 확인하세요.

## Railway 백엔드 배포 체크리스트

### 프로젝트 설정
- [ ] Railway 프로젝트 생성
- [ ] GitHub 저장소 연결
- [ ] Root Directory를 `api`로 설정
- [ ] Build Command 확인 (railway.json 사용)
- [ ] Start Command 확인 (railway.json 사용)

### 데이터베이스
- [ ] PostgreSQL 데이터베이스 추가 (또는 SQLite 사용)
- [ ] `DATABASE_URL` 환경 변수 설정

### 환경 변수
- [ ] `DATABASE_URL` 설정
- [ ] `ALLOWED_ORIGINS` 설정 (프론트엔드 URL)
- [ ] `OPENAI_API_KEY` 설정 (필요시)
- [ ] `ANTHROPIC_API_KEY` 설정 (필요시)
- [ ] `EMBEDDING_MODEL` 설정 (선택사항)
- [ ] `EMBEDDING_ENSEMBLE` 설정 (선택사항)
- [ ] `EMBEDDING_AUTO_LEARN` 설정 (선택사항)

### 배포 확인
- [ ] 배포 완료 확인
- [ ] 헬스 체크 통과 (`/health`)
- [ ] API 문서 접근 가능 (`/docs`)
- [ ] CORS 설정 확인

## Vercel 프론트엔드 배포 체크리스트

### 프로젝트 설정
- [ ] Vercel 프로젝트 생성
- [ ] GitHub 저장소 연결
- [ ] Root Directory를 `frontend`로 설정
- [ ] Framework Preset: Vite (자동 감지)
- [ ] Build Command: `npm run build` (자동 감지)
- [ ] Output Directory: `dist` (자동 감지)

### 환경 변수
- [ ] `VITE_API_URL` 설정 (Railway 백엔드 URL)

### 배포 확인
- [ ] 배포 완료 확인
- [ ] 프론트엔드 접근 가능
- [ ] API 연결 테스트

## 통합 테스트 체크리스트

### 기능 테스트
- [ ] 프론트엔드에서 분석 시작 가능
- [ ] 백엔드에서 분석 처리 가능
- [ ] 분석 결과가 프론트엔드에 표시됨
- [ ] 리포트 다운로드 기능 작동
- [ ] 에러 핸들링 정상 작동

### 네트워크 테스트
- [ ] CORS 오류 없음
- [ ] API 요청 정상 작동
- [ ] 타임아웃 설정 적절함

### 보안 테스트
- [ ] 환경 변수 노출 없음
- [ ] CORS 설정 적절함
- [ ] API 키 보안 확인

## 모니터링 설정

### Railway
- [ ] 로그 확인 가능
- [ ] 배포 상태 모니터링 설정

### Vercel
- [ ] 로그 확인 가능
- [ ] 배포 상태 모니터링 설정

## 문서화

- [ ] 배포 가이드 문서 작성
- [ ] 환경 변수 설명 문서 작성
- [ ] 문제 해결 가이드 작성

## 최종 확인

- [ ] 모든 체크리스트 항목 완료
- [ ] 프로덕션 환경에서 전체 기능 테스트
- [ ] 성능 확인
- [ ] 보안 확인

---

**참고**: 이 체크리스트는 배포 전에 확인해야 할 주요 항목들을 포함합니다. 프로젝트의 특성에 따라 추가 항목이 필요할 수 있습니다.
