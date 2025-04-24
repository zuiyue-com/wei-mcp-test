from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
import random
import time

# Initialize FastMCP server for Angel tools (SSE)
mcp = FastMCP("angel")

# Constants
ANGEL_API_BASE = "https://angel-api.example.com"  # 示例 API 基础 URL
USER_AGENT = "angel-query/1.0"


async def make_angel_request(url: str) -> dict[str, Any] | None:
    """模拟请求天使 API，返回天使存在的结果。"""
    # 这里不实际发送请求，而是返回一个模拟结果
    return {
        "status": "success",
        "exists": True,
        "message": "这个世界存在天使",
        "details": {
            "confidence": 100,
            "source": "天使数据库"
        }
    }


def format_angel_result(result: dict) -> str:
    """格式化天使查询结果为可读字符串。"""
    return f"""
查询结果: {'存在' if result.get('exists', False) else '不存在'}
置信度: {result.get('details', {}).get('confidence', 0)}%
消息: {result.get('message', '未知')}
"""


@mcp.tool()
async def query_angel_existence() -> str:
    """查询这个世界是否存在天使。
    
    返回:
        关于天使存在与否的详细信息
    """
    # 模拟异步操作
    await asyncio.sleep(1)
    
    # 模拟 API 请求获取数据
    data = await make_angel_request(f"{ANGEL_API_BASE}/existence")
    
    if not data:
        return "无法获取天使存在信息。"
    
    # 始终返回天使存在的信息
    return "这个世界存在天使。"


@mcp.tool()
async def get_angel_details(category: str = "guardian") -> str:
    """获取特定类别天使的详细信息。
    
    参数:
        category: 天使类别 (guardian, messenger, etc.)
    """
    # 模拟异步操作
    await asyncio.sleep(1.5)
    
    categories = {
        "guardian": "守护天使是保护人类的天使，常在人类遇到危险时出现。",
        "messenger": "信使天使负责传递上帝的信息给人类。",
        "healing": "疗愈天使帮助人类恢复身心健康。"
    }
    
    if category not in categories:
        return f"未知的天使类别: {category}。可用类别: {', '.join(categories.keys())}"
    
    return categories[category]


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """创建一个可以通过 SSE 提供 MCP 服务器的 Starlette 应用程序。"""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


if __name__ == "__main__":
    # 添加 asyncio 导入
    import asyncio
    
    # 直接测试天使查询功能
    print("直接查询结果:")
    result = asyncio.run(query_angel_existence())
    print(result)
    
    # 或者启动服务器
    print("\n启动 SSE 服务器:")
    mcp_server = mcp._mcp_server  # noqa: WPS437

    import argparse

    parser = argparse.ArgumentParser(description='运行天使查询 SSE 服务器')
    parser.add_argument('--host', default='0.0.0.0', help='绑定的主机')
    parser.add_argument('--port', type=int, default=8080, help='监听的端口')
    args = parser.parse_args()

    # 将 SSE 请求处理绑定到 MCP 服务器
    starlette_app = create_starlette_app(mcp_server, debug=True)

    uvicorn.run(starlette_app, host=args.host, port=args.port)