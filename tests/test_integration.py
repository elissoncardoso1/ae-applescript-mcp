"""Integração contra o After Effects real. Só roda com AE aberto e AE_MCP_INTEGRATION=1.

Proteção: pula tudo se o projeto aberto tiver arquivo fora do tempdir ou alterações
não salvas; os testes só criam e descartam projetos temporários.
"""
import os
import tempfile

import pytest

from ae_mcp import server as s
from ae_mcp.runner import AEError

pytestmark = pytest.mark.skipif(os.environ.get("AE_MCP_INTEGRATION") != "1",
                                reason="defina AE_MCP_INTEGRATION=1 com o AE aberto")
TMP = os.path.realpath(tempfile.gettempdir())


@pytest.fixture(scope="module", autouse=True)
def scratch_project():
    ov = s.ae_get_project_overview()
    f = ov["project_file"]
    if ov["unsaved_changes"] or (f and not os.path.realpath(f).startswith(TMP)):
        pytest.skip("projeto do usuário aberto — não vou mexer")
    s.ae_new_project(discard_unsaved_changes=False)
    yield
    s.ae_new_project(discard_unsaved_changes=True)  # só descarta o que os testes criaram


@pytest.fixture
def comp():
    name = "T" + os.urandom(3).hex()
    s.ae_create_comp(name=name, width=1080, height=1920, duration=10, frame_rate=30)
    return name


def test_overview_lists_created_comp(comp):
    ov = s.ae_get_project_overview()
    c = [i for i in ov["items"] if i["name"] == comp][0]
    assert (c["type"], c["width"], c["height"], c["duration"]) == ("comp", 1080, 1920, 10)


def test_text_layer_centered_with_unicode(comp):
    s.ae_add_layer(layer_type="text", text="Clínica TAAL — 10 anos", comp_name=comp)
    s.ae_set_layer_properties(comp_name=comp, changes=[
        {"layer_index": 1, "justification": "center", "font_size": 90,
         "fill_color": "#F05378", "center_anchor": True, "position": [540, 960]}])
    L = s.ae_inspect_comp(comp_name=comp, response_format="detailed")["layers"][0]
    assert L["text"] == "Clínica TAAL — 10 anos" and L["type"] == "text"
    assert L["position"][:2] == [540, 960] and L["fill_color"] == "#F05378"


def test_keyframes_fade_in(comp):
    s.ae_add_layer(layer_type="solid", color="#26326E", comp_name=comp)
    s.ae_set_keyframes(comp_name=comp, tracks=[{"layer_index": 1, "property": "opacity", "easing": "ease",
                                                 "keyframes": [{"time": 0, "value": 0}, {"time": 1, "value": 100}]}])
    L = s.ae_inspect_comp(comp_name=comp, response_format="detailed")["layers"][0]
    anim = [a for a in L["animated"] if a["property"].endswith("Opacity")][0]
    assert [k["value"] for k in anim["keyframes"]] == [0, 100]


def test_shapes_null_adjustment_effect_and_remove(comp):
    for t in ("shape_rectangle", "shape_ellipse", "null_object", "adjustment"):
        s.ae_add_layer(layer_type=t, comp_name=comp, color="#4C6971", width=200, height=200)
    r = s.ae_apply_effect(comp_name=comp, layer_index=1, effect="Gaussian Blur", params={"Blurriness": 12})
    assert "Blurriness" in r["parameters"]
    types = [l["type"] for l in s.ae_inspect_comp(comp_name=comp)["layers"]]
    assert types == ["adjustment", "null_object", "shape", "shape"]
    s.ae_remove_layers(comp_name=comp, layer_indexes=[1, 2])
    assert s.ae_inspect_comp(comp_name=comp)["num_layers"] == 2


def test_queue_render_and_save(comp, tmp_path):
    q = s.ae_queue_render(comp_name=comp, output_path=str(tmp_path / "out.mov"))
    assert q["comp"] == comp and q["status"] == "QUEUED"
    p = str(tmp_path / "proj.aep")
    assert s.ae_save_project_as(path=p)["saved"].endswith("proj.aep")
    with pytest.raises(Exception, match="overwrite"):
        s.ae_save_project_as(path=p)


def test_errors_are_instructions(comp):
    with pytest.raises(Exception, match="ae_get_project_overview"):
        s.ae_inspect_comp(comp_name="não existe")
    with pytest.raises(Exception, match="layer_index"):
        s.ae_set_layer_properties(comp_name=comp, changes=[{"layer_index": 99, "opacity": 50}])
    with pytest.raises(Exception, match="Gaussian Blur"):
        s.ae_add_layer(layer_type="null_object", comp_name=comp)
        s.ae_apply_effect(comp_name=comp, layer_index=1, effect="Efeito Inventado")


def test_run_extendscript_disabled_by_default():
    with pytest.raises(Exception, match="AE_MCP_ENABLE_RUN_EXTENDSCRIPT"):
        s.ae_run_extendscript(code="return 1;")
