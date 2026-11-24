"""Servidor MCP: controla o Adobe After Effects via AppleScript (DoScript) no macOS."""
import json
import os
import subprocess
import time as time_mod
import uuid
from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver import Image
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from . import templates as T
from .runner import AEError, AERunner

APP_PATH = os.environ.get("AE_APP_PATH", "/Applications/Adobe After Effects 2027/Adobe After Effects 2027.app")
RUN_ENABLED = os.environ.get("AE_MCP_ENABLE_RUN_EXTENDSCRIPT") == "1"
runner = AERunner(APP_PATH, timeout=int(os.environ.get("AE_MCP_TIMEOUT", "60")),
                  override=os.environ.get("AE_MCP_OVERRIDE", "1") == "1")

mcp = MCPServer("after-effects-applescript", instructions=(
    "Controla o Adobe After Effects aberto no macOS. Comece com ae_get_project_overview. "
    "Camadas: layer_index começa em 1 (topo). Tempos em segundos. Cores em #RRGGBB. "
    "Depois de editar, confirme com ae_inspect_comp. Peça confirmação ao usuário antes de "
    "salvar por cima, descartar alterações ou apagar camadas."))

READ = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)
ADD = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
EDIT = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
DANGER = ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=False, open_world_hint=False)

CompName = Annotated[str | None, Field(description="Nome exato da composição. Use este OU comp_index.")]
CompIndex = Annotated[int | None, Field(ge=1, description="Índice do item no painel Projeto (base 1), como em ae_get_project_overview.")]
Fmt = Annotated[Literal["concise", "detailed"], Field(description="concise (padrão) ou detailed (mais campos).")]
Hex = Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$", description="Cor #RRGGBB, ex.: #F05378")]
Vec = list[float]


def _run(template: str, args: dict, undo: str | None = None):
    try:
        return runner.run(template, {k: v for k, v in args.items() if v is not None}, undo, T.HELPERS)
    except AEError as e:
        raise ToolError(str(e)) from None


def _target(comp_name, comp_index) -> dict:
    if comp_name is None and comp_index is None:
        raise ToolError('Informe comp_name ou comp_index. Ex.: {"comp_name": "Main"}. '
                        "Veja as comps com ae_get_project_overview.")
    return {"comp_name": comp_name, "comp_index": comp_index}


@mcp.tool(annotations=READ)
def ae_get_project_overview(response_format: Fmt = "concise") -> dict:
    """Visão geral do projeto aberto: versão do AE, arquivo, se há alterações não salvas,
    itens (comps com tamanho/duração/fps/nº de camadas; até 50) e fila de render.
    Use SEMPRE antes de editar, para descobrir nomes e índices."""
    return _run(T.OVERVIEW, {"detailed": response_format == "detailed"})


@mcp.tool(annotations=READ)
def ae_inspect_comp(comp_name: CompName = None, comp_index: CompIndex = None,
                    response_format: Fmt = "concise") -> dict:
    """Lê uma composição: configurações e camadas (índice, nome, tipo, tempos, posição, opacidade,
    texto, efeitos, propriedades animadas). 'detailed' acrescenta escala, rotação, âncora, fonte,
    cor e os valores dos keyframes (até 20 por propriedade). Use para verificar o resultado de edições."""
    return _run(T.INSPECT_COMP, {**_target(comp_name, comp_index), "detailed": response_format == "detailed"})


@mcp.tool(annotations=READ)
def ae_get_layer_properties(layer_index: Annotated[int, Field(ge=1)],
                            comp_name: CompName = None, comp_index: CompIndex = None,
                            filter: Annotated[str | None, Field(description="Trecho do caminho, ex.: 'Opacity', 'Effects/Gaussian Blur'")] = None,
                            time: Annotated[float | None, Field(ge=0, description="Segundos; padrão = tempo atual da comp")] = None) -> dict:
    """Lista as propriedades de uma camada como caminhos planos ('Transform/Opacity',
    'Effects/Gaussian Blur/Blurriness'…) com valor no tempo, nº de keyframes e expressão.
    Use para descobrir o caminho exato a passar em properties/expressions/ae_set_keyframes (até 200)."""
    return _run(T.GET_LAYER_PROPERTIES, {**locals(), **_target(comp_name, comp_index)})


@mcp.tool(annotations=READ)
def ae_render_frame(comp_name: CompName = None, comp_index: CompIndex = None,
                    time: Annotated[float | None, Field(ge=0, description="Segundos; padrão = tempo atual da comp")] = None,
                    max_side: Annotated[int, Field(ge=64, le=4096, description="Lado maior da imagem devolvida")] = 960) -> list:
    """Renderiza UM frame da comp e devolve a imagem (PNG) para você OLHAR o resultado:
    texto cortado, sobreposição, cores, enquadramento. Não grava nada no projeto."""
    png = os.path.join(runner._dir, uuid.uuid4().hex + ".png")
    info = _run(T.RENDER_FRAME, {**_target(comp_name, comp_index), "time": time, "png_path": png})
    deadline, last = time_mod.monotonic() + runner.timeout, -1
    while True:  # saveFrameToPng é assíncrono: espera o arquivo parar de crescer
        size = os.path.getsize(png) if os.path.exists(png) else -1
        if size > 0 and size == last:
            break
        if time_mod.monotonic() > deadline:
            raise ToolError("O After Effects não terminou de gerar o frame a tempo. Tente de novo com max_side menor.")
        last = size
        time_mod.sleep(0.25)
    if max(info["width"], info["height"]) > max_side:
        subprocess.run(["sips", "-Z", str(max_side), png], capture_output=True, check=True)
    data = open(png, "rb").read()
    os.remove(png)
    return [json.dumps(info, ensure_ascii=False), Image(data=data, format="png")]


@mcp.tool(annotations=ADD)
def ae_create_comp(name: Annotated[str, Field(min_length=1)],
                   width: Annotated[int, Field(ge=4, le=30000)], height: Annotated[int, Field(ge=4, le=30000)],
                   duration: Annotated[float, Field(gt=0, le=10800, description="Segundos")],
                   frame_rate: Annotated[float, Field(gt=0, le=999)] = 30,
                   background_color: Hex | None = None) -> dict:
    """Cria uma composição. Ex.: vertical 1080x1920, 10 s, 30 fps. Devolve comp_index e nome."""
    return _run(T.CREATE_COMP, locals(), undo=f"Criar comp {name}")


@mcp.tool(annotations=ADD)
def ae_add_layer(layer_type: Literal["text", "solid", "null_object", "adjustment", "shape_rectangle", "shape_ellipse"],
                 comp_name: CompName = None, comp_index: CompIndex = None,
                 text: Annotated[str | None, Field(description="Obrigatório para layer_type=text.")] = None,
                 name: str | None = None,
                 color: Annotated[str | None, Field(pattern=r"^#[0-9A-Fa-f]{6}$", description="#RRGGBB: cor do sólido/shape ou do preenchimento do texto")] = None,
                 width: Annotated[int | None, Field(ge=1, description="Solid/shape; padrão = largura da comp.")] = None,
                 height: Annotated[int | None, Field(ge=1)] = None,
                 position: Annotated[Vec | None, Field(min_length=2, max_length=3, description="[x, y] em pixels")] = None) -> dict:
    """Adiciona uma camada no topo da comp (vira layer_index 1; as outras descem um índice).
    Texto nasce com a âncora na linha de base; para centralizar, use ae_set_layer_properties
    com justification='center' e center_anchor=true."""
    args = {**locals(), **_target(comp_name, comp_index)}
    return _run(T.ADD_LAYER, args, undo=f"Adicionar camada {layer_type}")


class LayerChange(BaseModel):
    layer_index: int = Field(ge=1)
    name: str | None = None
    position: Vec | None = None
    scale: Vec | None = Field(None, description="Percentual, ex.: [100, 100]")
    rotation: float | None = None
    opacity: float | None = Field(None, ge=0, le=100)
    anchor_point: Vec | None = None
    in_point: float | None = None
    out_point: float | None = None
    text: str | None = None
    font: str | None = Field(None, description="Nome PostScript, ex.: Arial-BoldMT")
    font_size: float | None = Field(None, gt=0)
    fill_color: Hex | None = None
    justification: Literal["left", "center", "right"] | None = None
    parent_index: int | None = Field(None, ge=0, description="0 remove o pai")
    center_anchor: bool | None = Field(None, description="Põe a âncora no centro visual da camada (útil para centralizar texto).")
    expressions: dict[str, str] | None = Field(
        None, description='Caminho → expressão do AE, ex.: {"rotation": "time*90", "Transform/Position": "wiggle(2,20)"}; "" remove. Expressão inválida desfaz o lote inteiro.')
    properties: dict[str, float | list[float] | str] | None = Field(
        None, description='Caminho → valor, ex.: {"Effects/Gaussian Blur/Blurriness": 20}')


@mcp.tool(annotations=EDIT)
def ae_set_layer_properties(changes: Annotated[list[LayerChange], Field(min_length=1)],
                            comp_name: CompName = None, comp_index: CompIndex = None) -> dict:
    """Altera várias camadas de uma vez (valores estáticos): nome, transform, tempos, texto, fonte,
    cor, justificação, pai, âncora central e propriedades por caminho. Propriedades com keyframes
    devem ser mudadas com ae_set_keyframes."""
    args = {**_target(comp_name, comp_index), "changes": [LayerChange.model_validate(c).model_dump(exclude_none=True) for c in changes]}
    return _run(T.SET_LAYER_PROPERTIES, args, undo="Alterar camadas")


class Keyframe(BaseModel):
    time: float = Field(ge=0, description="Segundos")
    value: float | list[float] | str


class Track(BaseModel):
    layer_index: int = Field(ge=1)
    property: str = Field(description="position|scale|rotation|opacity|anchor_point ou caminho, ex.: 'Effects/Gaussian Blur/Blurriness'")
    keyframes: list[Keyframe] = Field(min_length=1)
    easing: Literal["linear", "ease", "hold"] = "linear"
    replace_existing: bool = Field(False, description="true apaga TODOS os keyframes existentes da propriedade antes (só com confirmação se não foram criados nesta conversa).")


@mcp.tool(annotations=EDIT)
def ae_set_keyframes(tracks: Annotated[list[Track], Field(min_length=1)],
                     comp_name: CompName = None, comp_index: CompIndex = None) -> dict:
    """Cria keyframes em lote. Ex. de fade-in de 1 s: property='opacity',
    keyframes=[{time:0,value:0},{time:1,value:100}], easing='ease'."""
    args = {**_target(comp_name, comp_index), "tracks": [Track.model_validate(t).model_dump() for t in tracks]}
    return _run(T.SET_KEYFRAMES, args, undo="Keyframes")


@mcp.tool(annotations=ADD)
def ae_apply_effect(layer_index: Annotated[int, Field(ge=1)],
                    effect: Annotated[str, Field(description="Nome em inglês ou matchName: 'Gaussian Blur', 'ADBE Fill', 'Glow'…")],
                    comp_name: CompName = None, comp_index: CompIndex = None,
                    params: Annotated[dict[str, float | list[float] | str] | None,
                                      Field(description='Ex.: {"Blurriness": 15}; cores como "#RRGGBB"')] = None) -> dict:
    """Adiciona um efeito à camada e define parâmetros. Devolve a lista de parâmetros disponíveis."""
    return _run(T.APPLY_EFFECT, {**locals(), **_target(comp_name, comp_index)}, undo=f"Efeito {effect}")


@mcp.tool(annotations=DANGER)
def ae_remove_layers(layer_indexes: Annotated[list[Annotated[int, Field(ge=1)]], Field(min_length=1)],
                     comp_name: CompName = None, comp_index: CompIndex = None) -> dict:
    """Apaga camadas pelos índices (pode desfazer com Cmd+Z no AE). Confirme com o usuário se
    as camadas não foram criadas nesta sessão."""
    return _run(T.REMOVE_LAYERS, {**_target(comp_name, comp_index), "layer_indexes": layer_indexes}, undo="Remover camadas")


@mcp.tool(annotations=ADD)
def ae_queue_render(output_path: Annotated[str, Field(description="Caminho absoluto do arquivo de saída; a pasta deve existir.")],
                    comp_name: CompName = None, comp_index: CompIndex = None,
                    output_module_template: str | None = None, render_settings_template: str | None = None,
                    overwrite: bool = False) -> dict:
    """Adiciona a comp à fila de render. NÃO inicia o render: renderizar bloqueia o AE.
    O usuário clica em Render no AE ou usa aerender."""
    if not os.path.isabs(output_path):
        raise ToolError("output_path precisa ser absoluto. Ex.: /Users/voce/Movies/video.mov")
    return _run(T.QUEUE_RENDER, {**locals(), **_target(comp_name, comp_index)}, undo="Enfileirar render")


@mcp.tool(annotations=DANGER)
def ae_save_project_as(path: Annotated[str, Field(description="Caminho absoluto terminando em .aep")],
                       overwrite: bool = False) -> dict:
    """Salva o projeto em um .aep. Recusa sobrescrever sem overwrite=true; só use overwrite
    com a confirmação explícita do usuário."""
    if not os.path.isabs(path):
        raise ToolError("path precisa ser absoluto. Ex.: /Users/voce/Projetos/video.aep")
    return _run(T.SAVE_AS, locals())


@mcp.tool(annotations=DANGER)
def ae_new_project(discard_unsaved_changes: bool = False) -> dict:
    """Fecha o projeto atual e começa um vazio. Recusa se houver alterações não salvas;
    discard_unsaved_changes=true só com a confirmação explícita do usuário."""
    return _run(T.NEW_PROJECT, locals())


@mcp.tool(annotations=DANGER)
def ae_open_project(path: Annotated[str, Field(description="Caminho absoluto de um .aep")],
                    discard_unsaved_changes: bool = False) -> dict:
    """Abre um .aep, com a mesma proteção de ae_new_project. Projetos com mídia ou fontes ausentes
    podem abrir um diálogo no AE que bloqueia os próximos comandos até o usuário fechá-lo."""
    return _run(T.OPEN_PROJECT, locals())


@mcp.tool(annotations=DANGER)
def ae_run_extendscript(code: Annotated[str, Field(description="Corpo de função ExtendScript (ES3); o valor do return é devolvido em JSON.")]) -> dict:
    """VÁLVULA DE ESCAPE: executa ExtendScript arbitrário dentro de um undo group. Desligada por padrão
    (AE_MCP_ENABLE_RUN_EXTENDSCRIPT=1 para habilitar). Prefira as ferramentas ae_*. Nunca use alert()
    nem diálogos: eles travam o AE."""
    if not RUN_ENABLED:
        raise ToolError("ae_run_extendscript está desligada. O usuário precisa habilitá-la com "
                        "AE_MCP_ENABLE_RUN_EXTENDSCRIPT=1 na configuração do servidor MCP. "
                        "Enquanto isso, use as ferramentas ae_*.")
    return {"result": _run(T.RUN_EXTENDSCRIPT, {"code": code}, undo="Script personalizado")}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
