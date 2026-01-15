# 전체 시스템 API 설치 가이드

이 문서는 Qoo10 AI Agent 프로젝트에서 설치해야 하는 모든 API 및 패키지 리스트를 정리합니다.

## 목차

1. [백엔드 Python 패키지](#1-백엔드-python-패키지)
2. [프론트엔드 Node.js 패키지](#2-프론트엔드-nodejs-패키지)
3. [외부 API 서비스](#3-외부-api-서비스)
4. [데이터베이스](#4-데이터베이스)
5. [환경 변수 설정](#5-환경-변수-설정)
6. [설치 순서](#6-설치-순서)

---

## 1. 백엔드 Python 패키지

### 위치
`/api/requirements.txt`

### 설치 명령어
```bash
cd api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 패키지 목록

#### 웹 프레임워크
- **fastapi>=0.109.1** - FastAPI 웹 프레임워크
- **uvicorn[standard]==0.24.0** - ASGI 서버
- **pydantic==2.5.0** - 데이터 검증 및 설정 관리
- **python-multipart==0.0.6** - 멀티파트 폼 데이터 처리

#### HTTP 클라이언트
- **httpx==0.25.2** - 비동기 HTTP 클라이언트

#### 웹 크롤링
- **beautifulsoup4==4.12.2** - HTML 파싱
- **lxml==4.9.3** - XML/HTML 파서
- **selenium==4.15.2** - 브라우저 자동화

#### 이미지 처리
- **pillow>=10.2.0** - 이미지 처리 라이브러리

#### 환경 설정
- **python-dotenv==1.0.0** - 환경 변수 관리

#### 파일 처리
- **aiofiles==23.2.1** - 비동기 파일 I/O

#### 보안
- **defusedxml==0.7.1** - XML 보안 처리 (requirements.txt에 중복 항목 존재, 중복 제거 권장)

#### 데이터 처리
- **numpy==1.26.2** - 수치 연산
- **pandas==2.1.3** - 데이터 분석

#### AI 서비스
- **openai==1.3.5** - OpenAI API 클라이언트
- **anthropic==0.7.7** - Anthropic (Claude) API 클라이언트

#### 데이터베이스
- **psycopg2-binary>=2.9.11** - PostgreSQL 어댑터 (보안 패치 적용 버전) 또는 **psycopg>=3.1.0** - PostgreSQL 어댑터 (psycopg3, 마이그레이션 시)
- **sqlalchemy==2.0.23** - ORM (Object-Relational Mapping)

#### 리포트 생성
- **reportlab==4.4.7** - PDF 생성
- **openpyxl==3.1.5** - Excel 파일 처리

---

## 2. 프론트엔드 Node.js 패키지

### 위치
`/frontend/package.json`

### 설치 명령어
```bash
cd frontend
npm install
```

### 프로덕션 의존성 (dependencies)

#### React 프레임워크
- **react@^18.2.0** - React 라이브러리
- **react-dom@^18.2.0** - React DOM 렌더러
- **react-router-dom@^6.20.0** - React 라우팅

#### HTTP 클라이언트
- **axios@^1.6.2** - HTTP 클라이언트

#### 상태 관리
- **zustand@^4.4.7** - 경량 상태 관리 라이브러리

#### 스타일링
- **tailwindcss@^3.3.6** - 유틸리티 우선 CSS 프레임워크
- **autoprefixer@^10.4.16** - CSS 자동 접두사 추가
- **postcss@^8.4.32** - CSS 변환 도구

### 개발 의존성 (devDependencies)

#### TypeScript
- **typescript@^5.3.3** - TypeScript 컴파일러
- **@types/react@^18.2.43** - React TypeScript 타입 정의
- **@types/react-dom@^18.2.17** - React DOM TypeScript 타입 정의

#### 빌드 도구
- **vite@^5.0.8** - 빠른 빌드 도구
- **@vitejs/plugin-react@^4.2.1** - Vite React 플러그인

---

## 3. 외부 API 서비스

### OpenAI API

#### 용도
- AI 기반 SEO 최적화
- 상품 분석 및 추천 생성
- 리포트 생성

#### 설정 방법
1. [OpenAI Platform](https://platform.openai.com/)에서 계정 생성
2. API 키 발급
3. 환경 변수에 설정: `OPENAI_API_KEY=your_api_key_here`

#### 비용
- 사용량 기반 과금
- 모델별로 가격 상이 (GPT-4, GPT-3.5 등)

### Anthropic API (Claude)

#### 용도
- AI 기반 SEO 최적화
- 상품 분석 및 추천 생성
- 리포트 생성

#### 설정 방법
1. [Anthropic Console](https://console.anthropic.com/)에서 계정 생성
2. API 키 발급
3. 환경 변수에 설정: `ANTHROPIC_API_KEY=your_api_key_here`

#### 비용
- 사용량 기반 과금
- 모델별로 가격 상이 (Claude 3 Opus, Sonnet, Haiku 등)

---

## 4. 데이터베이스

### PostgreSQL

#### 용도
- 분석 결과 저장
- 히스토리 관리
- 통계 데이터 저장
- 알림 관리

#### 설정 방법

##### 로컬 개발

> **참고**: 최신 안정 버전의 PostgreSQL(예: PostgreSQL 16) 또는 프로젝트에서 지원하는 버전을 사용하는 것을 권장합니다. 특정 버전이 필요한 경우 프로젝트 문서를 확인하세요.

###### macOS

```bash
# PostgreSQL 설치 (Homebrew - macOS 전용)
brew install postgresql@16  # 또는 최신 안정 버전
brew services start postgresql@16

# 데이터베이스 생성
createdb qoo10_ai_agent

# 환경 변수 설정
DATABASE_URL=postgresql://user:password@localhost:5432/qoo10_ai_agent
```

###### Linux

**apt를 사용하는 경우 (Ubuntu/Debian):**
```bash
# PostgreSQL 설치
sudo apt update
sudo apt install postgresql postgresql-contrib

# PostgreSQL 서비스 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 데이터베이스 생성
sudo -u postgres createdb qoo10_ai_agent
```

**yum을 사용하는 경우 (CentOS/RHEL):**
```bash
# PostgreSQL 설치
sudo yum install postgresql-server postgresql-contrib

# PostgreSQL 초기화 및 시작
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 데이터베이스 생성
sudo -u postgres createdb qoo10_ai_agent
```

**Docker를 사용하는 경우:**
```bash
# PostgreSQL 컨테이너 실행
docker run --name qoo10-postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=qoo10_ai_agent \
  -p 5432:5432 \
  -d postgres:16

# 환경 변수 설정
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/qoo10_ai_agent
```

###### Windows

**공식 설치 프로그램 사용:**
1. [PostgreSQL 공식 웹사이트](https://www.postgresql.org/download/windows/)에서 설치 프로그램 다운로드
2. 설치 마법사를 따라 PostgreSQL 설치 (최신 안정 버전 권장)
3. 설치 중 비밀번호 설정
4. pgAdmin 또는 명령 프롬프트에서 데이터베이스 생성:
   ```sql
   CREATE DATABASE qoo10_ai_agent;
   ```

**WSL(Windows Subsystem for Linux) 사용 (권장):**
```bash
# WSL에서 Linux 설치 방법과 동일하게 진행
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb qoo10_ai_agent
```

**환경 변수 설정 (모든 플랫폼 공통):**
```bash
# DATABASE_URL 형식:
# postgresql://[사용자명]:[비밀번호]@[호스트]:[포트]/[데이터베이스명]
DATABASE_URL=postgresql://user:password@localhost:5432/qoo10_ai_agent

# 실제 값 예시:
# - user: postgres (기본값) 또는 생성한 사용자명
# - password: 설치 시 설정한 비밀번호
# - host: localhost (로컬) 또는 원격 서버 주소
# - port: 5432 (PostgreSQL 기본 포트)
# - database: qoo10_ai_agent (생성한 데이터베이스명)
```

##### 프로덕션 (Railway)
1. Railway 프로젝트에서 "New" 버튼 클릭
2. "Database" → "Add PostgreSQL" 선택
3. PostgreSQL 서비스가 생성되면 자동으로 `DATABASE_URL` 환경 변수가 설정됨

#### 대안: SQLite (개발용)
- PostgreSQL이 설정되지 않은 경우 자동으로 SQLite 사용
- 별도 설치 불필요
- 프로덕션 환경에서는 PostgreSQL 권장

---

## 5. 환경 변수 설정

### 백엔드 환경 변수

`.env` 파일을 `api/` 디렉토리에 생성하거나 Railway/Vercel 환경 변수로 설정:

```bash
# AI API 키
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 데이터베이스
DATABASE_URL=postgresql://user:password@host:port/database
# 또는 SQLite 사용 시 생략 가능

# CORS 설정
ALLOWED_ORIGINS=https://your-frontend-url.vercel.app,http://localhost:5173

# 관리자 API 키 (선택사항)
ADMIN_API_KEY=your_admin_api_key_here

# 포트 (Railway는 자동 설정)
PORT=8080
```

### 프론트엔드 환경 변수

`.env` 파일을 `frontend/` 디렉토리에 생성하거나 Vercel 환경 변수로 설정:

```bash
# 백엔드 API URL
VITE_API_URL=https://your-railway-backend-url.railway.app
# 또는 로컬 개발 시
VITE_API_URL=http://localhost:8080
```

---

## 6. 설치 순서

### 전체 시스템 설치 가이드

> **참고**: 아래의 모든 명령어는 프로젝트 루트 디렉토리(`qoo10-ai-agent/`)에서 실행하는 것을 전제로 합니다.

#### 1단계: 백엔드 설정

```bash
# 1. 백엔드 디렉토리로 이동
cd api

# 2. 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Python 패키지 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
# .env 파일 생성 및 필요한 변수 설정
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/qoo10_ai_agent
ALLOWED_ORIGINS=http://localhost:5173
EOF

# 5. 서버 실행 (개발 모드)
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

#### 2단계: 프론트엔드 설정

```bash
# 1. 프론트엔드 디렉토리로 이동
cd frontend

# 2. Node.js 패키지 설치
npm install

# 3. 환경 변수 설정
# .env 파일 생성
cat > .env << EOF
VITE_API_URL=http://localhost:8080
EOF

# 4. 개발 서버 실행
npm run dev
```

#### 3단계: 데이터베이스 설정 (선택사항)

```bash
# PostgreSQL 설치 (macOS)
brew install postgresql@14
brew services start postgresql@14

# 데이터베이스 생성
createdb qoo10_ai_agent

# 연결 테스트
psql qoo10_ai_agent
```

#### 4단계: 외부 API 키 발급

1. **OpenAI API 키 발급**
   - <https://platform.openai.com/> 접속
   - 계정 생성 및 로그인
   - API Keys 메뉴에서 새 키 생성
   - `.env` 파일에 `OPENAI_API_KEY` 설정

2. **Anthropic API 키 발급**
   - <https://console.anthropic.com/> 접속
   - 계정 생성 및 로그인
   - API Keys 메뉴에서 새 키 생성
   - `.env` 파일에 `ANTHROPIC_API_KEY` 설정

---

## 7. 검증 및 테스트

### 백엔드 검증

```bash
# 1. 서버 실행 확인
curl http://localhost:8080/health

# 2. API 문서 확인
# 브라우저에서 http://localhost:8080/docs 접속

# 3. 패키지 설치 확인
pip list | grep -E "fastapi|uvicorn|openai|anthropic"
```

### 프론트엔드 검증

```bash
# 1. 개발 서버 실행 확인
# 브라우저에서 http://localhost:5173 접속

# 2. 패키지 설치 확인
npm list --depth=0
```

### 통합 테스트

```bash
# 1. 백엔드와 프론트엔드가 모두 실행 중인지 확인
# 2. 프론트엔드에서 URL 입력 및 분석 시작 테스트
# 3. API 응답 확인
```

---

## 8. 문제 해결

### Python 패키지 설치 오류

```bash
# pip 업그레이드
pip install --upgrade pip

# 가상 환경 재생성
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Node.js 패키지 설치 오류

```bash
# node_modules 삭제 후 재설치
rm -rf node_modules package-lock.json
npm install

# npm 캐시 클리어
npm cache clean --force
```

### 데이터베이스 연결 오류

```bash
# PostgreSQL 서비스 상태 확인
brew services list | grep postgresql

# PostgreSQL 재시작
brew services restart postgresql@14

# 연결 테스트
psql -h localhost -U postgres -d qoo10_ai_agent
```

### API 키 오류

- OpenAI/Anthropic API 키가 올바르게 설정되었는지 확인
- API 키에 충분한 크레딧이 있는지 확인
- 환경 변수가 올바르게 로드되었는지 확인 (`python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"`)

---

## 9. 요약

### 필수 설치 항목

1. **Python 패키지** (21개)
   - 웹 프레임워크, 크롤링, AI 서비스, 데이터베이스 등

2. **Node.js 패키지** (11개)
   - React, TypeScript, 빌드 도구 등

3. **외부 API 서비스** (2개)
   - OpenAI API
   - Anthropic API

4. **데이터베이스** (1개)
   - PostgreSQL (또는 SQLite)

### 선택적 설치 항목

- 관리자 API 키 (ADMIN_API_KEY)
- 프록시 서버 (크롤링용)

---

## 참고 문서

- [README.md](./README.md) - 프로젝트 개요
- [DEPLOYMENT.md](./DEPLOYMENT.md) - 배포 가이드
- [api/README.md](./api/README.md) - 백엔드 상세 가이드
- [frontend/README.md](./frontend/README.md) - 프론트엔드 상세 가이드
