"""Templates reais + HELPERS executados no Node contra um AE falso mínimo."""
import json
import shutil
import subprocess

import pytest

from ae_mcp import templates as T
from ae_mcp.jsx import build_script

node = shutil.which("node")
pytestmark = pytest.mark.skipif(not node, reason="node não instalado")

FAKE_AE = """
var __files = {};
function File(p) { this.p = p; this.buf = ''; this.exists = false; }
File.prototype.open = function () { return true; };
File.prototype.write = function (s) { this.buf += s; };
File.prototype.close = function () { __files[this.p] = this.buf; };
function CompItem() {} function TextLayer() {} function ShapeLayer() {} function CameraLayer() {} function LightLayer() {}
function FolderItem() {} function FootageItem() {} function SolidSource() {} function AVLayer() {}
var PropertyType = {PROPERTY: 1, INDEXED_GROUP: 2}, PropertyValueType = {NO_VALUE: 0, OneD: 1, TwoD: 2, ThreeD: 3, TwoD_SPATIAL: 4, ThreeD_SPATIAL: 5, COLOR: 6, TEXT_DOCUMENT: 7};
var CloseOptions = {DO_NOT_SAVE_CHANGES: 2}, KeyframeInterpolationType = {LINEAR: 1, BEZIER: 2, HOLD: 3};
function KeyframeEase(s, i) { this.speed = s; this.influence = i; }
var __log = [];
function Prop(name, vt, keys) {
  this.name = name; this.propertyType = 1; this.propertyValueType = vt; this.canVaryOverTime = true;
  this.keys = keys || []; this.value = vt === 6 ? [1, 0, 0, 1] : 0;
}
Prop.prototype = {
  get numKeys() { return this.keys.length; },
  removeKey: function (i) { this.keys.splice(i - 1, 1); },
  setValueAtTime: function (t, v) { for (var i = 0; i < this.keys.length; i++) if (this.keys[i].t === t) { this.keys[i].v = v; return; } this.keys.push({t: t, v: v}); this.keys.sort(function (a, b) { return a.t - b.t; }); },
  nearestKeyIndex: function (t) { for (var i = 0; i < this.keys.length; i++) if (this.keys[i].t === t) return i + 1; return 1; },
  setTemporalEaseAtKey: function (k, a) { __log.push('ease:' + k + ':' + a.length); },
  setInterpolationTypeAtKey: function (k) { __log.push('interp:' + k); }
};
function Layer(name, comp) { this.name = name; this.comp = comp; }
Layer.prototype.remove = function () { var L = this.comp.L; for (var i = 0; i < L.length; i++) if (L[i] === this) { L.splice(i, 1); return; } };
Layer.prototype.property = function (n) { return this.props ? this.props[n] : null; };
var comp = new CompItem(); comp.name = 'C'; comp.L = [];
comp.layer = function (i) { var l = this.L[i - 1]; l.index = i; return l; };
Object.defineProperty(comp, 'numLayers', {get: function () { return this.L.length; }});
var app = {beginUndoGroup: function () {}, endUndoGroup: function () {}, project: {numItems: 1, dirty: false, closed: 0,
  item: function () { return comp; }, close: function () { this.closed++; }}};
"""


def run(template, args, setup=""):
    script = build_script(template, args, "/r.json", helpers=T.HELPERS)
    src = FAKE_AE + setup + script + "\nprocess.stdout.write(JSON.stringify([__files['/r.json'], __log, app.project.closed]));"
    out = subprocess.run([node, "-e", src], capture_output=True, text=True, check=True).stdout
    raw, log, closed = json.loads(out)
    return json.loads(raw), log, closed


@pytest.mark.parametrize("name", [n for n in dir(T) if n.isupper()])
def test_every_template_compiles_as_es3_function(name):
    src = T.HELPERS + "\nnew Function('args', " + json.dumps(getattr(T, name)) + ");"
    subprocess.run([node, "-e", src], check=True)


def test_remove_layers_ignores_duplicate_indexes():
    setup = "comp.L = [new Layer('A', comp), new Layer('B', comp), new Layer('C', comp)];"
    res, _, _ = run(T.REMOVE_LAYERS, {"comp_name": "C", "layer_indexes": [2, 2]}, setup)
    assert res["data"] == {"removed": ["B"], "num_layers": 2}


@pytest.mark.parametrize("tpl", ["NEW_PROJECT", "OPEN_PROJECT"])
def test_dirty_project_is_never_closed_without_flag(tpl):
    setup = "app.project.dirty = true; var __F = File; File = function (p) { __F.call(this, p); this.exists = true; }; File.prototype = __F.prototype;"
    res, _, closed = run(getattr(T, tpl), {"path": "/x.aep"}, setup)
    assert res["ok"] is False and "discard_unsaved_changes" in res["error"]["message"] and closed == 0


KEYED = """
var op = new Prop('Opacity', 1, [{t: 0, v: 0}, {t: 5, v: 100}]);
var col = new Prop('Color', 6, []);
var L1 = new Layer('A', comp); L1.props = {'ADBE Transform Group': {property: function (n) { return n === 'ADBE Opacity' ? op : null; }, propertyType: 2}, 'Color': col};
comp.L = [L1];
"""


def test_set_keyframes_keeps_user_keys_by_default_and_eases_only_new_ones():
    track = {"layer_index": 1, "property": "opacity", "easing": "ease", "keyframes": [{"time": 2, "value": 50}]}
    res, log, _ = run(T.SET_KEYFRAMES, {"comp_name": "C", "tracks": [track]}, KEYED)
    assert res["data"]["tracks"][0]["num_keys"] == 3  # 0 e 5 do usuário preservados
    assert log == ["ease:2:1"]  # só o keyframe novo (índice 2) recebeu ease


def test_color_ease_uses_single_keyframe_ease():
    track = {"layer_index": 1, "property": "Color", "easing": "ease", "keyframes": [{"time": 0, "value": "#FF0000"}]}
    _, log, _ = run(T.SET_KEYFRAMES, {"comp_name": "C", "tracks": [track]}, KEYED)
    assert log == ["ease:1:1"]


def test_args_literal_is_pure_ascii():
    script = build_script("return 1;", {"s": "a b — 🎬"}, "/r.json")
    assert script.isascii()
