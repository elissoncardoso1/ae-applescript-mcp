"""Tarefas de avaliação multi-etapa via cliente MCP stdio real, verificadas lendo o projeto.

Uso (com o AE aberto e sem trabalho não salvo): uv run python evals/run_evals.py
Cada tarefa começa com ae_new_project; nunca toca em projeto do usuário (veja guard()).
"""
import asyncio
import json
import os
import sys
import tempfile

from mcp import Client, StdioServerParameters
from mcp.types import TextContent

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = tempfile.mkdtemp(prefix="ae-evals-")


class Fail(Exception):
    pass


async def call(c, tool, **args):
    r = await c.call_tool(tool, args)
    text = "".join(b.text for b in r.content if isinstance(b, TextContent))
    if r.is_error:
        raise Fail(f"{tool}: {text}")
    return r.structured_content if r.structured_content is not None else json.loads(text)


async def err(c, tool, **args):
    r = await c.call_tool(tool, args)
    if not r.is_error:
        raise Fail(f"{tool} deveria falhar")
    return "".join(b.text for b in r.content if isinstance(b, TextContent))


def check(cond, msg):
    if not cond:
        raise Fail(msg)


def anim(layer, suffix):
    return [a for a in layer.get("animated", []) if a["property"].endswith(suffix)][0]


async def t1_taal(c):
    """Comp 1080x1920 10 s, texto 'Clínica TAAL — 10 anos' centralizado, fade-in 1 s, render enfileirado."""
    await call(c, "ae_create_comp", name="TAAL 10 anos", width=1080, height=1920, duration=10)
    await call(c, "ae_add_layer", comp_name="TAAL 10 anos", layer_type="text", text="Clínica TAAL — 10 anos")
    await call(c, "ae_set_layer_properties", comp_name="TAAL 10 anos", changes=[
        {"layer_index": 1, "justification": "center", "font_size": 80, "center_anchor": True, "position": [540, 960]}])
    await call(c, "ae_set_keyframes", comp_name="TAAL 10 anos", tracks=[
        {"layer_index": 1, "property": "opacity", "easing": "ease",
         "keyframes": [{"time": 0, "value": 0}, {"time": 1, "value": 100}]}])
    await call(c, "ae_queue_render", comp_name="TAAL 10 anos", output_path=f"{OUT}/taal.mp4")
    comp = await call(c, "ae_inspect_comp", comp_name="TAAL 10 anos", response_format="detailed")
    L = comp["layers"][0]
    check((comp["width"], comp["height"], comp["duration"]) == (1080, 1920, 10), "dimensões")
    check(L["text"] == "Clínica TAAL — 10 anos" and L["justification"] == "center", "texto")
    check(L["position"][:2] == [540, 960], f"posição {L['position']}")
    check([(k["time"], k["value"]) for k in anim(L, "Opacity")["keyframes"]] == [(0, 0), (1, 100)], "fade")
    ov = await call(c, "ae_get_project_overview")
    check(ov["render_queue"][-1]["status"] == "QUEUED", "fila de render")


async def t2_lower_third(c):
    """Lower third: barra azul + nome, entrando da esquerda em 0,5 s com ease."""
    n = "Lower third"
    await call(c, "ae_create_comp", name=n, width=1920, height=1080, duration=5)
    await call(c, "ae_add_layer", comp_name=n, layer_type="shape_rectangle", width=800, height=120,
               color="#26326E", position=[560, 900], name="Barra")
    await call(c, "ae_add_layer", comp_name=n, layer_type="text", text="Dra. Ana Souza", name="Nome", position=[200, 915])
    await call(c, "ae_set_keyframes", comp_name=n, tracks=[
        {"layer_index": 2, "property": "position", "easing": "ease",
         "keyframes": [{"time": 0, "value": [-400, 900]}, {"time": 0.5, "value": [560, 900]}]},
        {"layer_index": 1, "property": "position", "easing": "ease",
         "keyframes": [{"time": 0, "value": [-760, 915]}, {"time": 0.5, "value": [200, 915]}]}])
    comp = await call(c, "ae_inspect_comp", comp_name=n, response_format="detailed")
    check([l["name"] for l in comp["layers"]] == ["Nome", "Barra"], "ordem")
    check(anim(comp["layers"][1], "Position")["keyframes"][1]["value"][:2] == [560, 900], "barra")
    check(anim(comp["layers"][0], "Position")["num_keys"] == 2, "nome")


async def t3_pulse(c):
    """Elipse rosa pulsando: escala 100→120→100 em 1 s, linear."""
    await call(c, "ae_create_comp", name="Pulso", width=1080, height=1080, duration=3)
    await call(c, "ae_add_layer", comp_name="Pulso", layer_type="shape_ellipse", width=300, height=300, color="#F05378")
    await call(c, "ae_set_keyframes", comp_name="Pulso", tracks=[{"layer_index": 1, "property": "scale", "keyframes": [
        {"time": 0, "value": [100, 100]}, {"time": 0.5, "value": [120, 120]}, {"time": 1, "value": [100, 100]}]}])
    L = (await call(c, "ae_inspect_comp", comp_name="Pulso", response_format="detailed"))["layers"][0]
    check(L["type"] == "shape", "tipo")
    check([k["value"][0] for k in anim(L, "Scale")["keyframes"]] == [100, 120, 100], "escala")


async def t4_effects(c):
    """Fundo sólido verde-cinza com Gaussian Blur 25 e Fill rosa."""
    await call(c, "ae_create_comp", name="Fundo", width=1920, height=1080, duration=5)
    await call(c, "ae_add_layer", comp_name="Fundo", layer_type="solid", color="#4C6971", name="BG")
    r = await call(c, "ae_apply_effect", comp_name="Fundo", layer_index=1, effect="Gaussian Blur", params={"Blurriness": 25})
    check("Blurriness" in r["parameters"], "parâmetros blur")
    await call(c, "ae_apply_effect", comp_name="Fundo", layer_index=1, effect="ADBE Fill", params={"Color": "#F05378"})
    L = (await call(c, "ae_inspect_comp", comp_name="Fundo"))["layers"][0]
    check(L["effects"] == ["Gaussian Blur", "Fill"], f"efeitos {L.get('effects')}")


async def t5_parent(c):
    """Null controlador girando 360° em 4 s com dois textos como filhos."""
    n = "Orbita"
    await call(c, "ae_create_comp", name=n, width=1080, height=1080, duration=4)
    await call(c, "ae_add_layer", comp_name=n, layer_type="text", text="A", position=[740, 540])
    await call(c, "ae_add_layer", comp_name=n, layer_type="text", text="B", position=[340, 540])
    await call(c, "ae_add_layer", comp_name=n, layer_type="null_object", name="Controle", position=[540, 540])
    await call(c, "ae_set_layer_properties", comp_name=n, changes=[
        {"layer_index": 2, "parent_index": 1}, {"layer_index": 3, "parent_index": 1}])
    await call(c, "ae_set_keyframes", comp_name=n, tracks=[{"layer_index": 1, "property": "rotation", "keyframes": [
        {"time": 0, "value": 0}, {"time": 4, "value": 360}]}])
    comp = await call(c, "ae_inspect_comp", comp_name=n, response_format="detailed")
    check([l.get("parent_index") for l in comp["layers"]] == [None, 1, 1], "parentesco")
    check(anim(comp["layers"][0], "Rotation")["keyframes"][1]["value"] == 360, "rotação")


async def t6_sequence(c):
    """Três textos em sequência: 0–2 s, 2–4 s, 4–6 s."""
    n = "Sequencia"
    await call(c, "ae_create_comp", name=n, width=1920, height=1080, duration=6)
    for w in ("Três", "Dois", "Um"):
        await call(c, "ae_add_layer", comp_name=n, layer_type="text", text=w)
    await call(c, "ae_set_layer_properties", comp_name=n, changes=[
        {"layer_index": 1, "in_point": 0, "out_point": 2}, {"layer_index": 2, "in_point": 2, "out_point": 4},
        {"layer_index": 3, "in_point": 4, "out_point": 6}])
    comp = await call(c, "ae_inspect_comp", comp_name=n)
    got = [(l["text"], l["in_point"], l["out_point"]) for l in comp["layers"]]
    check(got == [("Um", 0, 2), ("Dois", 2, 4), ("Três", 4, 6)], f"tempos {got}")


async def t7_cleanup(c):
    """Cria 4 camadas, remove as 2 do meio e renomeia as restantes."""
    n = "Limpeza"
    await call(c, "ae_create_comp", name=n, width=1280, height=720, duration=2)
    for i in range(4):
        await call(c, "ae_add_layer", comp_name=n, layer_type="null_object", name=f"N{i}")
    await call(c, "ae_remove_layers", comp_name=n, layer_indexes=[2, 3])
    await call(c, "ae_set_layer_properties", comp_name=n, changes=[{"layer_index": 1, "name": "Topo"}, {"layer_index": 2, "name": "Base"}])
    comp = await call(c, "ae_inspect_comp", comp_name=n)
    check([l["name"] for l in comp["layers"]] == ["Topo", "Base"], "nomes")


async def t8_countdown(c):
    """Contagem regressiva 3-2-1 com keyframes hold no Source Text."""
    n = "Contagem"
    await call(c, "ae_create_comp", name=n, width=1080, height=1080, duration=3)
    await call(c, "ae_add_layer", comp_name=n, layer_type="text", text="3")
    await call(c, "ae_set_keyframes", comp_name=n, tracks=[{"layer_index": 1, "property": "Text/Source Text", "easing": "hold",
        "keyframes": [{"time": 0, "value": "3"}, {"time": 1, "value": "2"}, {"time": 2, "value": "1"}]}])
    L = (await call(c, "ae_inspect_comp", comp_name=n, response_format="detailed"))["layers"][0]
    check([k["value"] for k in anim(L, "Source Text")["keyframes"]] == ["3", "2", "1"], "contagem")


async def t9_save_reopen(c):
    """Salva em .aep temporário, reabre e confirma a comp."""
    await call(c, "ae_create_comp", name="Persistida", width=640, height=360, duration=1)
    p = f"{OUT}/persist.aep"
    await call(c, "ae_save_project_as", path=p)
    await call(c, "ae_new_project")
    r = await call(c, "ae_open_project", path=p)
    check(r["num_items"] == 1, "itens")
    ov = await call(c, "ae_get_project_overview")
    check(ov["items"][0]["name"] == "Persistida" and not ov["unsaved_changes"], "reaberto")


async def t10_recover(c):
    """Erro guiado: comp errada → mensagem aponta overview → corrige."""
    await call(c, "ae_create_comp", name="Certa", width=640, height=360, duration=1)
    msg = await err(c, "ae_inspect_comp", comp_name="Errada")
    check("ae_get_project_overview" in msg, f"mensagem {msg}")
    ov = await call(c, "ae_get_project_overview")
    name = ov["items"][0]["name"]
    check((await call(c, "ae_inspect_comp", comp_name=name))["name"] == "Certa", "recuperação")


async def t11_adjustment(c):
    """Camada de ajuste com Glow só entre 2 e 4 s."""
    n = "Brilho"
    await call(c, "ae_create_comp", name=n, width=1920, height=1080, duration=6)
    await call(c, "ae_add_layer", comp_name=n, layer_type="solid", color="#26326E")
    await call(c, "ae_add_layer", comp_name=n, layer_type="adjustment")
    await call(c, "ae_apply_effect", comp_name=n, layer_index=1, effect="Glow")
    await call(c, "ae_set_layer_properties", comp_name=n, changes=[{"layer_index": 1, "in_point": 2, "out_point": 4}])
    L = (await call(c, "ae_inspect_comp", comp_name=n))["layers"][0]
    check((L["type"], L["in_point"], L["out_point"], L["effects"]) == ("adjustment", 2, 4, ["Glow"]), f"ajuste {L}")


TASKS = [t1_taal, t2_lower_third, t3_pulse, t4_effects, t5_parent, t6_sequence, t7_cleanup,
         t8_countdown, t9_save_reopen, t10_recover, t11_adjustment]


async def main(only=None):
    params = StdioServerParameters(command="uv", args=["run", "--directory", ROOT, "ae-applescript-mcp"])
    rows = []
    async with Client(params) as c:
        ov = await call(c, "ae_get_project_overview")
        f = ov["project_file"]
        if ov["unsaved_changes"] or (f and not os.path.realpath(f).startswith(os.path.realpath(tempfile.gettempdir()))):
            sys.exit("Projeto do usuário aberto/não salvo — abortando para não mexer nele.")
        for t in TASKS:
            if only and t.__name__ not in only:
                continue
            await call(c, "ae_new_project", discard_unsaved_changes=True)
            try:
                await t(c)
                rows.append((t.__name__, "ok", ""))
            except Fail as e:
                rows.append((t.__name__, "FALHOU", str(e)))
        await call(c, "ae_new_project", discard_unsaved_changes=True)
    ok = sum(r[1] == "ok" for r in rows)
    for r in rows:
        print(" | ".join(r))
    print(f"Sucesso: {ok}/{len(rows)}")
    return 0 if ok == len(rows) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:] or None)))
