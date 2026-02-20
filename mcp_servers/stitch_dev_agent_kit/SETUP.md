# Stitch dev-agent-kit MCP 서버 설정 가이드

이 가이드는 Google Stitch dev-agent-kit 서브에이전트를 MCP 형태로 Cursor에 연결하는 방법을 설명합니다.

## 사전 요구사항

1. Python 3.9 이상
2. Cursor IDE
3. Stitch API 키 (Stitch 웹사이트에서 발급)

## 설치 단계

### 1. 의존성 설치



### 2. 환경 변수 설정

`.env` 파일을 생성하거나 환경 변수를 설정합니다:

```bash
# 방법 1: .env 파일 생성
# 방법 1: .env 파일 생성
# 참고: .env.example 파일이 저장소에 포함되어 있습니다
cp .env.example .env
# .env 파일을 편집하여 STITCH_API_KEY를 설정
# .env 파일을 편집하여 STITCH_API_KEY를 설정

# 방법 2: 환경 변수 직접 설정
# 주의: 이 방법은 API 키가 셸 히스토리에 저장될 수 있으므로 권장하지 않습니다
# 가능하면 .env 파일 사용을 권장합니다
export STITCH_API_URL="https://stitch.withgoogle.com"
export STITCH_API_KEY="your-api-key-here"  # 프로덕션에서는 사용하지 마세요
```

### 3. Cursor MCP 설정

Cursor의 `mcp.json` 파일에 다음 설정이 자동으로 추가되었습니다:



**중요**: `STITCH_API_KEY` 값을 실제 API 키로 변경해야 합니다.

### 4. Cursor 재시작

설정을 적용하려면 Cursor를 재시작하세요.

## 사용 방법

### Cursor에서 사용

Cursor를 재시작한 후, AI 채팅에서 다음과 같이 사용할 수 있습니다:

1. **서브에이전트 생성**
   - "Stitch에서 새로운 서브에이전트를 생성해줘"
   - "stitch_create_sub_agent 도구를 사용해서..."

2. **서브에이전트 목록 조회**
   - "Stitch의 모든 서브에이전트 목록을 보여줘"
   - "stitch_list_sub_agents 도구를 사용해서..."

3. **서브에이전트 실행**
   - "Stitch 서브에이전트를 실행해줘"
   - "stitch_run_sub_agent 도구를 사용해서..."

### 직접 테스트

서버를 직접 테스트하려면 (프로젝트 루트에서):

```bash
cd mcp_servers/stitch_dev_agent_kit
python3 server.py
```

## 사용 가능한 도구

### 1. stitch_create_sub_agent
새로운 서브에이전트를 생성합니다.

**예시:**
```json
{
  "name": "my-sub-agent",
  "description": "내 서브에이전트",
  "config": {
    "model": "gemini-2.0-flash",
    "temperature": 0.7
  }
}
```

### 2. stitch_list_sub_agents
모든 서브에이전트 목록을 조회합니다.

### 3. stitch_get_sub_agent
특정 서브에이전트의 정보를 조회합니다.

**예시:**
```json
{
  "agent_id": "agent-123"
}
```

### 4. stitch_run_sub_agent
서브에이전트를 실행하고 결과를 반환합니다.

**예시:**
```json
{
  "agent_id": "agent-123",
  "input": {
    "query": "안녕하세요",
    "context": "추가 컨텍스트"
  },
  "session_id": "session-456"
}
```

### 5. stitch_delete_sub_agent
서브에이전트를 삭제합니다.

**예시:**
```json
{
  "agent_id": "agent-123"
}
```

## 문제 해결

### 1. API 키 오류
**증상**: "STITCH_API_KEY 환경 변수가 설정되지 않았습니다" 오류

**해결 방법**:
- `mcp.json` 파일의 `STITCH_API_KEY` 값을 확인하세요
- 환경 변수가 올바르게 설정되었는지 확인하세요

### 2. 연결 오류
**증상**: "Connection refused" 또는 타임아웃 오류

**해결 방법**:
- Stitch API URL이 올바른지 확인하세요
- 네트워크 연결을 확인하세요
- 방화벽 설정을 확인하세요

### 3. 권한 오류
**증상**: "401 Unauthorized" 또는 "403 Forbidden" 오류

**해결 방법**:
- API 키가 유효한지 확인하세요
- API 키에 필요한 권한이 있는지 확인하세요
- Stitch 웹사이트에서 API 키를 재발급받으세요

### 4. Python 경로 오류
**증상**: "python3: command not found" 오류

**해결 방법**:
- Python 3가 설치되어 있는지 확인하세요
- `which python3` 명령어로 Python 경로를 확인하세요
- `mcp.json`의 `command`를 올바른 Python 경로로 변경하세요

## 추가 설정

### 커스텀 API URL 사용

Stitch API URL을 변경하려면 `mcp.json`의 `STITCH_API_URL` 값을 수정하세요:

```json
{
  "env": {
    "STITCH_API_URL": "https://custom-stitch-api.example.com",
    "STITCH_API_KEY": "your-api-key"
  }
}
```

### 타임아웃 설정

서버 코드에서 타임아웃을 조정할 수 있습니다. `server.py` 파일의 `httpx.AsyncClient` 호출 부분을 수정하세요.

## 참고 자료

- [Model Context Protocol 문서](https://modelcontextprotocol.io/)
- [Stitch dev-agent-kit 문서](https://stitch.withgoogle.com)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
