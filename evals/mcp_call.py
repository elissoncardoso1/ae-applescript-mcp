"""Harness CLI para agentes de teste: fala com o servidor MCP via stdio.
  uv run python evals/mcp_call.py list
  uv run python evals/mcp_call.py call <ferramenta> '<json de argumentos>'
"""
import asyncio
import json
import os
import sys

from mcp import Client, StdioServerParameters
from mcp.types import TextContent

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def main():
    params = StdioServerParameters(command="uv", args=["run", "--directory", ROOT, "ae-applescript-mcp"])
    async with Client(params) as c:
        if sys.argv[1] == "list":
            for t in (await c.list_tools()).tools:
                print(f"## {t.name}\n{t.description}\n{json.dumps(t.input_schema, ensure_ascii=False)}\n")
            return
        r = await c.call_tool(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})
        text = "".join(b.text for b in r.content if isinstance(b, TextContent))
        print(("ERRO: " if r.is_error else "") + text)

asyncio.run(main())
