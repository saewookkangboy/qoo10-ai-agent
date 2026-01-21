# Vercel 배포 가이드

이 문서는 Qoo10 AI Agent 프론트엔드를 Vercel에 배포하는 방법을 설명합니다.

## 1. Vercel 프로젝트 생성

### 1.1 Vercel 계정 준비
1. [Vercel](https://vercel.com)에 로그인 또는 회원가입
2. GitHub 계정으로 연동 (권장)

### 1.2 프로젝트 연결
1. Vercel 대시보드에서 "Add New Project" 클릭
2. GitHub 저장소 선택
3. 프로젝트 설정:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite (자동 감지)
   - **Build Command**: `npm run build` (자동 감지)
   - **Output Directory**: `dist` (자동 감지)
   - **Install Command**: `npm install` (자동 감지)

## 2. 환경 변수 설정

Vercel 대시보드 → 프로젝트 → Settings → Environment Variables에서 추가:

```bash
VITE_API_URL=https://your-railway-backend-url.railway.app
```

> **중요**: Railway 백엔드 배포 후 URL을 설정해야 합니다.

## 3. 배포

- Vercel은 GitHub에 푸시할 때마다 자동으로 배포합니다
- 또는 Vercel 대시보드에서 "Deploy" 버튼 클릭

## 4. 배포 확인

1. Vercel 대시보드 → Deployments 탭에서 배포 상태 확인
2. 배포된 URL 접속하여 기능 테스트
3. 브라우저 개발자 도구에서 네트워크 오류 확인

## 5. 커스텀 도메인 설정 (선택사항)

1. Vercel 프로젝트 → Settings → Domains
2. 원하는 도메인 입력
3. DNS 설정 안내에 따라 도메인 설정

## 6. 환경 변수 업데이트

백엔드 URL이 변경되면:
1. Vercel 대시보드 → Settings → Environment Variables
2. `VITE_API_URL` 값 업데이트
3. 자동으로 재배포됩니다

## 7. 문제 해결

### 빌드 실패
- Vercel 로그 확인: Deployments → 해당 배포 → Logs
- 로컬에서 `npm run build` 테스트
- `package.json`의 의존성 확인

### API 연결 오류
- `VITE_API_URL` 환경 변수가 올바른지 확인
- CORS 설정 확인 (백엔드)
- 브라우저 개발자 도구에서 네트워크 탭 확인

### 라우팅 오류 (404)
- `vercel.json`의 `rewrites` 설정 확인
- SPA 라우팅이 올바르게 설정되었는지 확인

## 참고 자료

- [Vercel 문서](https://vercel.com/docs)
- [Vite 배포 가이드](https://vitejs.dev/guide/static-deploy.html)
