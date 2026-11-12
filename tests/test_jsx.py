"""Executa o ExtendScript gerado no Node (ES3 é subconjunto) com File/app falsos."""
import json
import shutil
import subprocess

import pytest

from ae_mcp.jsx import PRELUDE, build_script

node = shutil.which("node")
pytestmark = pytest.mark.skipif(not node, reason="node não instalado")

FAKES = """
var __files = {}; var __calls = [];
function File(p) { this.p = p; this.buf = ''; }
File.prototype.open = function () { return true; };
File.prototype.write = function (s) { this.buf += s; };
File.prototype.close = function () { __files[this.p] = this.buf; };
var app = { beginUndoGroup: function (n) { __calls.push('begin:' + n); },
            endUndoGroup: function () { __calls.push('end'); } };
"""


def run_node(src: str) -> str:
    return subprocess.run([node, "-e", src], capture_output=True, text=True, check=True).stdout


def run_script(template: str, args: dict, undo: str | None = None) -> tuple[dict, list]:
    script = build_script(template, args, "/tmp/r.json", undo)
    out = run_node(FAKES + script + "\nprocess.stdout.write(JSON.stringify([__files['/tmp/r.json'], __calls]));")
    raw, calls = json.loads(out)
    return json.loads(raw), calls


TRICKY = 'aspas " \\ barra \n quebra \t tab   sep Clínica — 🎬 </script>'


def test_serializer_roundtrips_tricky_values():
    value = {"s": TRICKY, "n": [1, 2.5, -0.0001, True, False, None], "o": {"a": {"b": []}}}
    out = run_node(PRELUDE + f"process.stdout.write(__aeJSON({json.dumps(value)}));")
    assert json.loads(out) == value


def test_serializer_maps_non_finite_and_undefined_to_null():
    out = run_node(PRELUDE + "process.stdout.write(__aeJSON([NaN, Infinity, undefined, {x: undefined, y: 1}]));")
    assert json.loads(out) == [None, None, None, {"y": 1}]


def test_args_are_data_not_code():
    payload = "'); throw 1; //\"); app.quit(); ("
    res, _ = run_script("return args.s;", {"s": payload})
    assert res == {"ok": True, "data": payload}


def test_template_error_becomes_structured_error():
    res, _ = run_script("throw new Error('falhou aqui');", {})
    assert res["ok"] is False and res["error"]["message"] == "falhou aqui"


def test_undo_group_closes_even_on_error():
    _, calls = run_script("throw new Error('x');", {}, undo="Criar comp")
    assert calls == ["begin:MCP: Criar comp", "end"]
