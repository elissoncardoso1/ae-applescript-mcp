"""Chamadas pelo protocolo MCP (in-memory), sem AE: validação de argumentos."""
import anyio
from mcp import Client

from ae_mcp.server import mcp


def call(tool, args):
    async def go():
        async with Client(mcp) as c:
            return await c.call_tool(tool, args)
    return anyio.run(go)


def test_every_layer_type_survives_argument_parsing():
    # "null" como string era convertido em None pelo SDK; nenhum valor do enum pode ser JSON.
    tools = anyio.run(lambda: _list())
    enum = tools["ae_add_layer"].input_schema["properties"]["layer_type"]["enum"]
    for v in enum:
        r = call("ae_add_layer", {"layer_type": v})  # sem comp: deve falhar no alvo, não na validação
        assert "comp_name ou comp_index" in r.content[0].text, (v, r.content[0].text)


async def _list():
    async with Client(mcp) as c:
        return {t.name: t for t in (await c.list_tools()).tools}


def test_tool_count_and_prefix():
    tools = anyio.run(lambda: _list())
    assert len(tools) == 15 and all(n.startswith("ae_") for n in tools)
