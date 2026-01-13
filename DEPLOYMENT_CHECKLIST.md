# 배포 체크리스트

## 프론트엔드 배포 (Vercel) ✅

### 사전 준비
- [ ] GitHub 저장소 준비
- [ ] Vercel 계정 생성
- [ ] 프로젝트 코드 푸시

### Vercel 설정
- [ ] Vercel 프로젝트 생성
- [ ] Root Directory: `frontend` 설정
- [ ] Framework Preset: Vite 확인
- [ ] 환경 변수 `VITE_API_URL` 설정 (백엔드 배포 후)

### 배포
- [ ] 초기 배포 실행
- [ ] 배포 성공 확인
- [ ] 배포된 URL 접속 테스트

### 확인
- [ ] 홈페이지 로드 확인
- [ ] URL 입력 기능 테스트
- [ ] API 연결 확인 (백엔드 배포 후)

---

## 백엔드 배포 (Railway) ⏳

### 사전 준비
- [ ] Railway 계정 생성
- [ ] GitHub 저장소 연결
- [ ] API 키 준비 (OpenAI, Anthropic)

### Railway 설정
- [ ] Railway 프로젝트 생성
- [ ] GitHub 저장소 연결
- [ ] Root Directory: `api` 설정
- [ ] PostgreSQL 데이터베이스 추가
- [ ] 환경 변수 설정:
  - [ ] `DATABASE_URL` (자동 설정)
  - [ ] `OPENAI_API_KEY`
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `ALLOWED_ORIGINS` (Vercel URL)
  - [ ] `PORT` (자동 설정)

### 배포
- [ ] 초기 배포 실행
- [ ] 배포 성공 확인
- [ ] Railway URL 확인

### 확인
- [ ] Health check 엔드포인트 테스트
- [ ] Swagger 문서 접속 확인
- [ ] API 엔드포인트 테스트

---

## 연결 및 통합

### 프론트엔드-백엔드 연결
- [ ] Vercel 환경 변수에 Railway URL 설정
- [ ] 프론트엔드 재배포
- [ ] API 호출 테스트

### CORS 설정
- [ ] 백엔드 CORS 설정 확인
- [ ] Vercel URL이 허용 목록에 포함되었는지 확인

### 데이터베이스
- [ ] PostgreSQL 연결 확인
- [ ] 테이블 자동 생성 확인
- [ ] 데이터 저장 테스트

---

## 최종 확인

### 기능 테스트
- [ ] URL 입력 및 분석 시작
- [ ] 분석 결과 조회
- [ ] 리포트 표시
- [ ] 에러 처리 확인

### 성능 확인
- [ ] 응답 시간 확인
- [ ] 로딩 상태 표시 확인
- [ ] 에러 메시지 확인

### 모니터링 설정
- [ ] Vercel 대시보드 모니터링 확인
- [ ] Railway 대시보드 모니터링 확인
- [ ] 로그 확인 방법 숙지

---

## 문제 해결

### 일반적인 문제
- [ ] 빌드 실패: 로그 확인 및 로컬 빌드 테스트
- [ ] API 연결 오류: 환경 변수 및 CORS 확인
- [ ] 데이터베이스 오류: 연결 문자열 및 권한 확인

### 참고 문서
- [Vercel 문서](https://vercel.com/docs)
- [Railway 문서](https://docs.railway.app)
- [프로젝트 DEPLOYMENT.md](./DEPLOYMENT.md)
