#!/usr/bin/env python3
"""
Stitch dev-agent-kit MCP Server
Google Stitch dev-agent-kit 서브에이전트를 MCP 형태로 연결하는 서버
"""
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from mcp import types as mcp_types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MCP 서버 인스턴스 생성
app = Server("stitch-dev-agent-kit")

# Stitch dev-agent-kit 설정
STITCH_API_URL = os.getenv("STITCH_API_URL", "https://stitch.withgoogle.com")
STITCH_API_KEY = os.getenv("STITCH_API_KEY", "")


@app.list_tools()
async def list_tools() -> List[mcp_types.Tool]:
    """사용 가능한 도구 목록 반환"""
    return [
        mcp_types.Tool(
            name="stitch_create_sub_agent",
            description="Stitch dev-agent-kit에서 새로운 서브에이전트를 생성합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "서브에이전트 이름"
                    },
                    "description": {
                        "type": "string",
                        "description": "서브에이전트 설명"
                    },
                    "config": {
                        "type": "object",
                        "description": "서브에이전트 설정 (선택사항)"
                    }
                },
                "required": ["name", "description"]
            }
        ),
        mcp_types.Tool(
            name="stitch_list_sub_agents",
            description="Stitch dev-agent-kit의 모든 서브에이전트 목록을 조회합니다",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        mcp_types.Tool(
            name="stitch_get_sub_agent",
            description="특정 서브에이전트의 정보를 조회합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "서브에이전트 ID"
                    }
                },
                "required": ["agent_id"]
            }
        ),
        mcp_types.Tool(
            name="stitch_run_sub_agent",
            description="서브에이전트를 실행하고 결과를 반환합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "실행할 서브에이전트 ID"
                    },
                    "input": {
                        "type": "object",
                        "description": "서브에이전트에 전달할 입력 데이터"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "세션 ID (선택사항)"
                    }
                },
                "required": ["agent_id", "input"]
            }
        ),
        mcp_types.Tool(
            name="stitch_delete_sub_agent",
            description="서브에이전트를 삭제합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "삭제할 서브에이전트 ID"
                    }
                },
                "required": ["agent_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[mcp_types.Content]:
    """도구 호출 처리"""
    try:
        if name == "stitch_create_sub_agent":
            result = await create_sub_agent(
                name=arguments.get("name"),
                description=arguments.get("description"),
                config=arguments.get("config", {})
            )
        elif name == "stitch_list_sub_agents":
            result = await list_sub_agents()
        elif name == "stitch_get_sub_agent":
            result = await get_sub_agent(agent_id=arguments.get("agent_id"))
        elif name == "stitch_run_sub_agent":
            result = await run_sub_agent(
                agent_id=arguments.get("agent_id"),
                input_data=arguments.get("input"),
                session_id=arguments.get("session_id")
            )
        elif name == "stitch_delete_sub_agent":
            result = await delete_sub_agent(agent_id=arguments.get("agent_id"))
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [
            mcp_types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )
        ]
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}", exc_info=True)
        return [
            mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "tool": name,
                    "arguments": arguments
                }, ensure_ascii=False)
            )
        ]


async def create_sub_agent(name: str, description: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """서브에이전트 생성"""
    import httpx
    
    if not STITCH_API_KEY:
        raise ValueError("STITCH_API_KEY 환경 변수가 설정되지 않았습니다")
    
    url = f"{STITCH_API_URL}/api/v1/sub-agents"
    headers = {
        "Authorization": f"Bearer {STITCH_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": name,
        "description": description,
        "config": config or {}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()


async def list_sub_agents() -> Dict[str, Any]:
    """서브에이전트 목록 조회"""
    import httpx
    
    if not STITCH_API_KEY:
        raise ValueError("STITCH_API_KEY 환경 변수가 설정되지 않았습니다")
    
    url = f"{STITCH_API_URL}/api/v1/sub-agents"
    headers = {
        "Authorization": f"Bearer {STITCH_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()


async def get_sub_agent(agent_id: str) -> Dict[str, Any]:
    """특정 서브에이전트 정보 조회"""
    import httpx
    
    if not STITCH_API_KEY:
        raise ValueError("STITCH_API_KEY 환경 변수가 설정되지 않았습니다")
    
    url = f"{STITCH_API_URL}/api/v1/sub-agents/{agent_id}"
    headers = {
        "Authorization": f"Bearer {STITCH_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()


async def run_sub_agent(agent_id: str, input_data: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """서브에이전트 실행"""
    import httpx
    
    if not STITCH_API_KEY:
        raise ValueError("STITCH_API_KEY 환경 변수가 설정되지 않았습니다")
    
    url = f"{STITCH_API_URL}/api/v1/sub-agents/{agent_id}/run"
    headers = {
        "Authorization": f"Bearer {STITCH_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": input_data
    }
    if session_id:
        payload["session_id"] = session_id
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=60.0)
        response.raise_for_status()
        return response.json()


async def delete_sub_agent(agent_id: str) -> Dict[str, Any]:
    """서브에이전트 삭제"""
    import httpx
    
    if not STITCH_API_KEY:
        raise ValueError("STITCH_API_KEY 환경 변수가 설정되지 않았습니다")
    
    url = f"{STITCH_API_URL}/api/v1/sub-agents/{agent_id}"
    headers = {
        "Authorization": f"Bearer {STITCH_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        return {"status": "deleted", "agent_id": agent_id}


async def main():
    """MCP 서버 실행"""
    logger.info("Stitch dev-agent-kit MCP 서버 시작 중...")
    
    # 환경 변수 확인
    if not STITCH_API_KEY:
        logger.warning("STITCH_API_KEY가 설정되지 않았습니다. 일부 기능이 작동하지 않을 수 있습니다.")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("서버 종료 중...")
    except Exception as e:
        logger.error(f"서버 오류: {e}", exc_info=True)
        sys.exit(1)
