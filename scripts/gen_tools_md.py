"""Gera docs/TOOLS.md a partir dos schemas reais do servidor: uv run python scripts/gen_tools_md.py"""
import json
import pathlib

import anyio
from mcp import Client

from ae_mcp.server import mcp


async def main():
    async with Client(mcp) as c:
        tools = (await c.list_tools()).tools
    out = ["# Ferramentas (gerado de `list_tools`; não edite à mão)\n"]
    for t in tools:
        a = t.annotations
        flags = f"readOnly={a.read_only_hint} · destructive={a.destructive_hint} · idempotent={a.idempotent_hint}"
        out += [f"## `{t.name}`\n", f"_{flags}_\n", (t.description or "").strip() + "\n",
                "```json", json.dumps(t.input_schema, ensure_ascii=False, indent=2), "```\n"]
    pathlib.Path(__file__).parent.parent.joinpath("docs/TOOLS.md").write_text("\n".join(out), encoding="utf-8")
    print(len(tools), "ferramentas")

anyio.run(main)
