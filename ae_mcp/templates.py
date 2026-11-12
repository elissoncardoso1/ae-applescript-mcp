"""Templates ExtendScript (ES3) fixos. Cada um é o corpo de function(args)."""

HELPERS = r"""
function __err(msg) { throw new Error(msg); }
function __itemIndex(it) {
  for (var i = 1; i <= app.project.numItems; i++) if (app.project.item(i) === it) return i;
  return null;
}
function __comp(a) {
  var i, it, p = app.project;
  if (a.comp_name !== undefined && a.comp_name !== null) {
    for (i = 1; i <= p.numItems; i++) { it = p.item(i); if (it instanceof CompItem && it.name === a.comp_name) return it; }
    __err("Comp '" + a.comp_name + "' não encontrada. Veja os nomes com ae_get_project_overview. Ex.: {\"comp_name\": \"Main\"}");
  }
  if (a.comp_index !== undefined && a.comp_index !== null) {
    if (a.comp_index < 1 || a.comp_index > p.numItems) __err("comp_index " + a.comp_index + " fora do intervalo: o projeto tem " + p.numItems + " item(ns). Veja os índices com ae_get_project_overview.");
    it = p.item(a.comp_index);
    if (!(it instanceof CompItem)) __err("O item " + a.comp_index + " ('" + it.name + "') não é uma composição. Veja os índices com ae_get_project_overview.");
    return it;
  }
  __err("Informe comp_name ou comp_index. Ex.: {\"comp_name\": \"Main\"}");
}
function __layer(c, idx) {
  if (!idx || idx < 1 || idx > c.numLayers) __err("layer_index " + idx + " inválido: a comp '" + c.name + "' tem " + c.numLayers + " camada(s); 1 é a do topo. Veja os índices com ae_inspect_comp.");
  return c.layer(idx);
}
function __rgb(hex) {
  if (typeof hex !== 'string' || !/^#?[0-9a-fA-F]{6}$/.test(hex)) __err("Cor inválida '" + hex + "'. Use #RRGGBB, ex.: \"#F05378\".");
  hex = hex.replace('#', '');
  return [parseInt(hex.substr(0, 2), 16) / 255, parseInt(hex.substr(2, 2), 16) / 255, parseInt(hex.substr(4, 2), 16) / 255];
}
function __hex(c) {
  var s = '#', i, h;
  for (i = 0; i < 3; i++) { h = Math.round(c[i] * 255).toString(16).toUpperCase(); s += h.length < 2 ? '0' + h : h; }
  return s;
}
function __r(v) {
  if (v instanceof Array) { var a = [], i; for (i = 0; i < v.length; i++) a.push(__r(v[i])); return a; }
  if (typeof v === 'number') return Math.round(v * 1000) / 1000;
  if (v && typeof v === 'object') return v.text !== undefined ? v.text : String(v);
  return v;
}
var __SHORT = {position: 'ADBE Transform Group/ADBE Position', scale: 'ADBE Transform Group/ADBE Scale',
  rotation: 'ADBE Transform Group/ADBE Rotate Z', opacity: 'ADBE Transform Group/ADBE Opacity',
  anchor_point: 'ADBE Transform Group/ADBE Anchor Point'};
function __prop(layer, path) {
  var parts = (__SHORT[path] || path).split('/'), cur = layer, i, nx;
  for (i = 0; i < parts.length; i++) {
    nx = cur.property(parts[i]);
    if (!nx && parts[i] === 'Effects') nx = cur.property('ADBE Effect Parade');
    if (!nx) __err("Propriedade '" + parts[i] + "' não existe no caminho '" + path + "'. Veja os caminhos com ae_inspect_comp (response_format detailed). Ex.: \"opacity\", \"Effects/Gaussian Blur/Blurriness\".");
    cur = nx;
  }
  if (cur.propertyType !== PropertyType.PROPERTY) __err("'" + path + "' é um grupo, não uma propriedade com valor. Ex.: \"Effects/Gaussian Blur/Blurriness\".");
  return cur;
}
function __set(p, v, label) {
  if (p.numKeys > 0) __err("'" + label + "' tem keyframes; para mudar o valor use ae_set_keyframes. Ex.: {\"tracks\": [{\"layer_index\": 1, \"property\": \"" + label + "\", \"keyframes\": [{\"time\": 0, \"value\": 0}]}]}");
  if (p.propertyValueType === PropertyValueType.COLOR && typeof v === 'string') v = __rgb(v).concat([1]);
  p.setValue(v);
}
function __layerType(l) {
  if (l instanceof TextLayer) return 'text';
  if (l instanceof ShapeLayer) return 'shape';
  if (l instanceof CameraLayer) return 'camera';
  if (l instanceof LightLayer) return 'light';
  if (l.nullLayer) return 'null';
  if (l.adjustmentLayer) return 'adjustment';
  if (l.source && l.source.mainSource instanceof SolidSource) return 'solid';
  return 'footage';
}
function __rqStatus(s) {
  var n = ['WILL_CONTINUE', 'NEEDS_OUTPUT', 'UNQUEUED', 'QUEUED', 'RENDERING', 'USER_STOPPED', 'ERR_STOPPED', 'DONE'], i;
  for (i = 0; i < n.length; i++) if (RQItemStatus[n[i]] === s) return n[i];
  return String(s);
}
function __animated(group, prefix, out, detailed) {
  for (var i = 1; i <= group.numProperties; i++) {
    var p = group.property(i), path = prefix ? prefix + '/' + p.name : p.name;
    if (p.propertyType === PropertyType.PROPERTY) {
      if (p.numKeys > 0) {
        var o = {property: path, num_keys: p.numKeys};
        if (detailed) { o.keyframes = []; for (var k = 1; k <= p.numKeys && k <= 20; k++) o.keyframes.push({time: __r(p.keyTime(k)), value: __r(p.keyValue(k))}); }
        out.push(o);
      }
    } else __animated(p, path, out, detailed);
  }
}
function __params(e) {
  var r = [], i, p;
  for (i = 1; i <= e.numProperties; i++) { p = e.property(i); if (p.propertyType === PropertyType.PROPERTY && p.propertyValueType !== PropertyValueType.NO_VALUE) r.push(p.name); }
  return r;
}
function __guardDirty(a) {
  if (app.project.dirty && !a.discard_unsaved_changes) __err("O projeto atual tem alterações não salvas. Salve antes com ae_save_project_as ou, SOMENTE com a confirmação do usuário, repita com discard_unsaved_changes=true.");
}
"""

OVERVIEW = r"""
var p = app.project, items = [], lim = 50, n = p.numItems, i, it, o, rq = [], r;
for (i = 1; i <= n && items.length < lim; i++) {
  it = p.item(i);
  o = {index: i, name: it.name, type: it instanceof CompItem ? 'comp' : (it instanceof FolderItem ? 'folder' : 'footage')};
  if (it instanceof CompItem) { o.width = it.width; o.height = it.height; o.duration = __r(it.duration); o.frame_rate = __r(it.frameRate); o.num_layers = it.numLayers; }
  if (args.detailed) {
    if (it.parentFolder && it.parentFolder !== p.rootFolder) o.folder = it.parentFolder.name;
    if (it instanceof FootageItem && it.file) o.file = it.file.fsName;
  }
  items.push(o);
}
for (i = 1; i <= p.renderQueue.numItems; i++) {
  r = p.renderQueue.item(i);
  rq.push({index: i, comp: r.comp.name, status: __rqStatus(r.status),
           output: r.numOutputModules && r.outputModule(1).file ? r.outputModule(1).file.fsName : null});
}
return {app_version: app.version, project_file: p.file ? p.file.fsName : null, unsaved_changes: p.dirty,
        num_items: n, items: items, truncated: n > lim,
        hint: n > lim ? 'Mostrando ' + lim + ' de ' + n + ' itens. Para uma comp específica use ae_inspect_comp com comp_name.' : undefined,
        render_queue: rq};
"""

INSPECT_COMP = r"""
var c = __comp(args), L = [], lim = 100, i, j, l, o, tr, td, fx, anim;
for (i = 1; i <= c.numLayers && i <= lim; i++) {
  l = c.layer(i); tr = l.property('ADBE Transform Group');
  o = {index: i, name: l.name, type: __layerType(l), enabled: l.enabled, in_point: __r(l.inPoint), out_point: __r(l.outPoint),
       position: __r(tr.property('ADBE Position').value), opacity: __r(tr.property('ADBE Opacity').value)};
  if (l.parent) o.parent_index = l.parent.index;
  if (args.detailed) { o.scale = __r(tr.property('ADBE Scale').value); o.rotation = __r(tr.property('ADBE Rotate Z').value); o.anchor_point = __r(tr.property('ADBE Anchor Point').value); }
  if (l instanceof TextLayer) {
    td = l.property('ADBE Text Properties').property('ADBE Text Document').value;
    o.text = td.text; o.font_size = __r(td.fontSize);
    if (args.detailed) { o.font = td.font; try { o.fill_color = __hex(td.fillColor); } catch (e) {} o.justification = td.justification === ParagraphJustification.CENTER_JUSTIFY ? 'center' : (td.justification === ParagraphJustification.RIGHT_JUSTIFY ? 'right' : 'left'); }
  }
  fx = l.property('ADBE Effect Parade');
  if (fx && fx.numProperties) { o.effects = []; for (j = 1; j <= fx.numProperties; j++) o.effects.push(fx.property(j).name); }
  anim = []; __animated(l, '', anim, args.detailed); if (anim.length) o.animated = anim;
  L.push(o);
}
return {name: c.name, index: __itemIndex(c), width: c.width, height: c.height, duration: __r(c.duration),
        frame_rate: __r(c.frameRate), background_color: __hex(c.bgColor), num_layers: c.numLayers, layers: L,
        truncated: c.numLayers > lim, hint: c.numLayers > lim ? 'Mostrando ' + lim + ' de ' + c.numLayers + ' camadas.' : undefined};
"""

CREATE_COMP = r"""
var c = app.project.items.addComp(args.name, args.width, args.height, 1, args.duration, args.frame_rate);
if (args.background_color) c.bgColor = __rgb(args.background_color);
return {comp_index: __itemIndex(c), name: c.name, width: c.width, height: c.height, duration: __r(c.duration), frame_rate: __r(c.frameRate)};
"""

ADD_LAYER = r"""
var c = __comp(args), t = args.layer_type, l, w = args.width || c.width, h = args.height || c.height, g, v, shp;
if (t === 'text') {
  if (!args.text) __err("layer_type 'text' exige o campo text. Ex.: {\"layer_type\": \"text\", \"text\": \"Olá\"}");
  l = c.layers.addText(args.text);
} else if (t === 'solid') {
  l = c.layers.addSolid(__rgb(args.color || '#FFFFFF'), args.name || 'Solid', w, h, c.pixelAspect);
} else if (t === 'adjustment') {
  l = c.layers.addSolid([1, 1, 1], args.name || 'Adjustment Layer', c.width, c.height, c.pixelAspect);
  l.adjustmentLayer = true;
} else if (t === 'null') {
  l = c.layers.addNull();
} else {
  l = c.layers.addShape();
  g = l.property('ADBE Root Vectors Group').addProperty('ADBE Vector Group');
  v = g.property('ADBE Vectors Group');
  if (t === 'shape_ellipse') { shp = v.addProperty('ADBE Vector Shape - Ellipse'); shp.property('ADBE Vector Ellipse Size').setValue([w, h]); }
  else { shp = v.addProperty('ADBE Vector Shape - Rect'); shp.property('ADBE Vector Rect Size').setValue([w, h]); }
  v.addProperty('ADBE Vector Graphic - Fill').property('ADBE Vector Fill Color').setValue(__rgb(args.color || '#FFFFFF').concat([1]));
}
if (args.name) l.name = args.name;
if (args.position) l.property('ADBE Transform Group').property('ADBE Position').setValue(args.position);
return {layer_index: l.index, name: l.name, type: __layerType(l)};
"""

SET_LAYER_PROPERTIES = r"""
var c = __comp(args), out = [], i, ch, l, sp, td, k, keys = ['position', 'scale', 'rotation', 'opacity', 'anchor_point'], r;
var J = {left: 'LEFT_JUSTIFY', center: 'CENTER_JUSTIFY', right: 'RIGHT_JUSTIFY'};
for (i = 0; i < args.changes.length; i++) {
  ch = args.changes[i]; l = __layer(c, ch.layer_index);
  if (ch.name !== undefined && ch.name !== null) l.name = ch.name;
  if (ch.text !== undefined || ch.font !== undefined || ch.font_size !== undefined || ch.fill_color !== undefined || ch.justification !== undefined) {
    if (!(l instanceof TextLayer)) __err("A camada " + l.index + " ('" + l.name + "') não é de texto; text/font/font_size/fill_color/justification só valem para camadas de texto.");
    sp = l.property('ADBE Text Properties').property('ADBE Text Document'); td = sp.value;
    if (ch.text !== undefined && ch.text !== null) td.text = ch.text;
    if (ch.font) td.font = ch.font;
    if (ch.font_size) td.fontSize = ch.font_size;
    if (ch.fill_color) { td.applyFill = true; td.fillColor = __rgb(ch.fill_color); }
    if (ch.justification) td.justification = ParagraphJustification[J[ch.justification]];
    __set(sp, td, 'Source Text');
  }
  for (k = 0; k < keys.length; k++) if (ch[keys[k]] !== undefined && ch[keys[k]] !== null) __set(__prop(l, keys[k]), ch[keys[k]], keys[k]);
  if (ch.in_point !== undefined && ch.in_point !== null) l.inPoint = ch.in_point;
  if (ch.out_point !== undefined && ch.out_point !== null) l.outPoint = ch.out_point;
  if (ch.parent_index !== undefined) l.parent = ch.parent_index ? __layer(c, ch.parent_index) : null;
  if (ch.properties) for (k in ch.properties) if (ch.properties.hasOwnProperty(k)) __set(__prop(l, k), ch.properties[k], k);
  if (ch.center_anchor) {
    r = l.sourceRectAtTime(Math.max(l.inPoint, 0), false);
    __set(__prop(l, 'anchor_point'), [r.left + r.width / 2, r.top + r.height / 2], 'anchor_point');
  }
  out.push({layer_index: l.index, name: l.name});
}
return {updated: out};
"""

SET_KEYFRAMES = r"""
var c = __comp(args), res = [], i, j, tk, l, p, kf, val, td, n, e, eases, interp;
for (i = 0; i < args.tracks.length; i++) {
  tk = args.tracks[i]; l = __layer(c, tk.layer_index); p = __prop(l, tk.property);
  if (!p.canVaryOverTime) __err("'" + tk.property + "' não aceita keyframes.");
  if (tk.replace_existing !== false) while (p.numKeys > 0) p.removeKey(1);
  for (j = 0; j < tk.keyframes.length; j++) {
    kf = tk.keyframes[j]; val = kf.value;
    if (p.propertyValueType === PropertyValueType.TEXT_DOCUMENT) { td = p.valueAtTime(kf.time, true); td.text = String(val); val = td; }
    else if (p.propertyValueType === PropertyValueType.COLOR && typeof val === 'string') val = __rgb(val).concat([1]);
    p.setValueAtTime(kf.time, val);
  }
  interp = tk.easing === 'hold' ? KeyframeInterpolationType.HOLD : (tk.easing === 'linear' ? KeyframeInterpolationType.LINEAR : KeyframeInterpolationType.BEZIER);
  for (j = 1; j <= p.numKeys; j++) {
    if (tk.easing === 'ease' && p.propertyValueType !== PropertyValueType.TEXT_DOCUMENT) {
      n = (p.propertyValueType === PropertyValueType.TwoD_SPATIAL || p.propertyValueType === PropertyValueType.ThreeD_SPATIAL || !(p.value instanceof Array)) ? 1 : p.value.length;
      eases = []; for (e = 0; e < n; e++) eases.push(new KeyframeEase(0, 33.33));
      p.setTemporalEaseAtKey(j, eases, eases);
    } else if (p.propertyValueType !== PropertyValueType.TEXT_DOCUMENT) p.setInterpolationTypeAtKey(j, interp, interp);
  }
  res.push({layer_index: l.index, layer: l.name, property: p.name, num_keys: p.numKeys});
}
return {tracks: res};
"""

APPLY_EFFECT = r"""
var c = __comp(args), l = __layer(c, args.layer_index), fx = l.property('ADBE Effect Parade'), e, k, pp, v;
if (!fx) __err("A camada " + l.index + " ('" + l.name + "') não aceita efeitos.");
if (!fx.canAddProperty(args.effect)) __err("Efeito '" + args.effect + "' não reconhecido. Use o matchName ou o nome exibido no AE em inglês, ex.: \"Gaussian Blur\" (\"ADBE Gaussian Blur 2\"), \"Fill\" (\"ADBE Fill\"), \"Glow\" (\"ADBE Glo2\").");
e = fx.addProperty(args.effect);
if (args.params) for (k in args.params) if (args.params.hasOwnProperty(k)) {
  pp = e.property(k);
  if (!pp) __err("Parâmetro '" + k + "' não existe em '" + e.name + "'. Disponíveis: " + __params(e).join(', ') + ". O efeito foi adicionado; corrija com ae_set_layer_properties (properties: {\"Effects/" + e.name + "/<parâmetro>\": valor}).");
  __set(pp, args.params[k], k);
}
return {layer_index: l.index, layer: l.name, effect: e.name, match_name: e.matchName, effect_index: e.propertyIndex, parameters: __params(e)};
"""

REMOVE_LAYERS = r"""
var c = __comp(args), idx = args.layer_indexes.slice(0).sort(function (a, b) { return b - a; }), out = [], i, l;
for (i = 0; i < idx.length; i++) __layer(c, idx[i]);
for (i = 0; i < idx.length; i++) { l = c.layer(idx[i]); out.push(l.name); l.remove(); }
return {removed: out, num_layers: c.numLayers};
"""

QUEUE_RENDER = r"""
var c = __comp(args), f = new File(args.output_path), rq, om;
if (!f.parent || !f.parent.exists) __err("A pasta de saída não existe: " + (f.parent ? f.parent.fsName : args.output_path) + ". Crie-a ou escolha outra. Ex.: \"/Users/voce/Movies/saida.mov\"");
if (f.exists && !args.overwrite) __err("O arquivo de saída já existe: " + f.fsName + ". Escolha outro nome ou, com a confirmação do usuário, repita com overwrite=true.");
rq = app.project.renderQueue.items.add(c);
if (args.render_settings_template) {
  try { rq.applyTemplate(args.render_settings_template); }
  catch (e1) { var rt = rq.templates.join(', '); rq.remove(); __err("Template de render '" + args.render_settings_template + "' não existe. Disponíveis: " + rt); }
}
om = rq.outputModule(1);
if (args.output_module_template) {
  try { om.applyTemplate(args.output_module_template); }
  catch (e2) { var t = om.templates.join(', '); rq.remove(); __err("Template de saída '" + args.output_module_template + "' não existe. Disponíveis: " + t); }
}
om.file = f;
return {rq_index: app.project.renderQueue.numItems, comp: c.name, status: __rqStatus(rq.status), output: om.file.fsName,
        note: 'Enfileirado, mas o render NÃO foi iniciado. O usuário renderiza no After Effects (botão Render) ou pelo aerender.'};
"""

SAVE_AS = r"""
var f = new File(args.path);
if (!/\.aep$/i.test(args.path)) __err("O caminho precisa terminar em .aep. Ex.: \"/Users/voce/Projetos/video.aep\"");
if (!f.parent || !f.parent.exists) __err("A pasta não existe: " + (f.parent ? f.parent.fsName : args.path));
if (f.exists && !args.overwrite) __err("Já existe um arquivo em " + f.fsName + ". Escolha outro nome ou, com a confirmação do usuário, repita com overwrite=true.");
app.project.save(f);
return {saved: app.project.file.fsName};
"""

NEW_PROJECT = r"""
__guardDirty(args);
app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
return {project_file: null, num_items: app.project.numItems};
"""

OPEN_PROJECT = r"""
var f = new File(args.path);
if (!f.exists) __err("Arquivo não encontrado: " + args.path + ". Use um caminho absoluto para um .aep existente.");
__guardDirty(args);
app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
app.open(f);
return {project_file: app.project.file ? app.project.file.fsName : null, num_items: app.project.numItems};
"""

RUN_EXTENDSCRIPT = r"""
return eval('(function () {\n' + args.code + '\n})')();
"""
