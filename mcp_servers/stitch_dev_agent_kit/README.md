# Stitch dev-agent-kit MCP Server

Google Stitch dev-agent-kit 서브에이전트를 MCP(Model Context Protocol) 형태로 연결하는 서버입니다.

## 설치

```bash
cd mcp_servers/stitch_dev_agent_kit
pip install -r requirements.txt
```

## 환경 변수 설정

`.env` 파일을 생성하거나 환경 변수를 설정합니다:

```bash
# Stitch API URL (기본값: https://stitch.withgoogle.com)
export STITCH_API_URL="https://stitch.withgoogle.com"

# Stitch API Key (필수)
export STITCH_API_KEY="your-api-key-here"
```

## Cursor에 연결

Cursor의 `mcp.json` 파일에 다음 설정을 추가합니다:

```json
{
  "mcpServers": {
    "stitch-dev-agent-kit": {
      "command": "python3",
      "args": [
       "args": [
        "/path/to/your/project/mcp_servers/stitch_dev_agent_kit/server.py"
       ],
      ],
      "env": {
        "STITCH_API_URL": "https://stitch.withgoogle.com",
        "STITCH_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## 사용 가능한 도구

### 1. stitch_create_sub_agent
새로운 서브에이전트를 생성합니다.

**파라미터:**
- `name` (필수): 서브에이전트 이름
- `description` (필수): 서브에이전트 설명
- `config` (선택): 서브에이전트 설정

### 2. stitch_list_sub_agents
모든 서브에이전트 목록을 조회합니다.

### 3. stitch_get_sub_agent
특정 서브에이전트의 정보를 조회합니다.

**파라미터:**
- `agent_id` (필수): 서브에이전트 ID

### 4. stitch_run_sub_agent
서브에이전트를 실행하고 결과를 반환합니다.

**파라미터:**
- `agent_id` (필수): 실행할 서브에이전트 ID
- `input` (필수): 서브에이전트에 전달할 입력 데이터
- `session_id` (선택): 세션 ID

### 5. stitch_delete_sub_agent
서브에이전트를 삭제합니다.

**파라미터:**
- `agent_id` (필수): 삭제할 서브에이전트 ID

## 테스트

서버를 직접 테스트하려면 (프로젝트 루트에서):

```bash
cd mcp_servers/stitch_dev_agent_kit
python3 server.py
```

## 문제 해결

1. **API 키 오류**: `STITCH_API_KEY` 환경 변수가 올바르게 설정되었는지 확인하세요.
2. **연결 오류**: Stitch API URL이 올바른지 확인하세요.
3. **권한 오류**: API 키에 필요한 권한이 있는지 확인하세요.
