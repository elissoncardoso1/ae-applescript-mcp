"""Montagem do ExtendScript: prelúdio fixo + template fixo + argumentos como literal JSON."""
import json

# ExtendScript é ES3: sem JSON nativo. Serializador próprio; tudo fora do ASCII
# imprimível sai como \uXXXX, então o arquivo de resultado é ASCII puro.
PRELUDE = r"""
function __aeStr(s) {
  var out = '"';
  for (var i = 0; i < s.length; i++) {
    var c = s.charAt(i), n = s.charCodeAt(i);
    if (c === '"' || c === '\\') out += '\\' + c;
    else if (n < 0x20 || n > 0x7e) { var h = n.toString(16); out += '\\u' + '0000'.substr(h.length) + h; }
    else out += c;
  }
  return out + '"';
}
function __aeJSON(v, d) {
  d = d || 0;
  if (d > 32 || v === null || v === undefined) return 'null';
  var t = typeof v, i, parts = [];
  if (t === 'boolean') return v ? 'true' : 'false';
  if (t === 'number') return isFinite(v) ? String(v) : 'null';
  if (t === 'string') return __aeStr(v);
  if (v instanceof Array) {
    for (i = 0; i < v.length; i++) parts.push(__aeJSON(v[i], d + 1));
    return '[' + parts.join(',') + ']';
  }
  if (t === 'object') {
    for (i in v) {
      if (v.hasOwnProperty(i) && v[i] !== undefined && typeof v[i] !== 'function')
        parts.push(__aeStr(String(i)) + ':' + __aeJSON(v[i], d + 1));
    }
    return '{' + parts.join(',') + '}';
  }
  return __aeStr(String(v));
}
"""


def build_script(template: str, args: dict, result_path: str, undo: str | None = None,
                 helpers: str = "") -> str:
    """`template` é o corpo de function(args); só código fixo do servidor entra aqui."""
    # ensure_ascii: o literal é ASCII puro, válido em ES3 (sem U+2028 cru).
    args_lit = json.dumps(args, ensure_ascii=True)
    body = template
    if undo:
        # Atômico: o sentinela garante que o grupo vira um passo de undo (grupo vazio não vira,
        # e o undo desfaria a ação ANTERIOR do usuário). Em erro, um undo desfaz só este grupo.
        body = (f"app.beginUndoGroup({json.dumps('MCP: ' + undo)});\n"
                "app.project.items.addFolder('__mcp_tx').remove();\n"
                "var __closed = false;\n"
                f"try {{\n{template}\n}} catch (__e) {{\n"
                "  app.endUndoGroup(); __closed = true; app.executeCommand(16);\n"
                "  var __m = String(__e && __e.message !== undefined ? __e.message : __e);\n"
                "  throw new Error(__m + ' (Nada foi alterado: a operação inteira foi desfeita.)');\n"
                "} finally { if (!__closed) app.endUndoGroup(); }")
    return f"""{PRELUDE}
{helpers}
(function () {{
  var __res;
  try {{
    __res = {{ok: true, data: (function (args) {{
{body}
    }})({args_lit})}};
  }} catch (e) {{
    __res = {{ok: false, error: {{message: String(e && e.message !== undefined ? e.message : e),
                                  line: e && e.line, name: e && e.name}}}};
  }}
  var __f = new File({json.dumps(result_path)});
  __f.encoding = 'UTF-8';
  __f.open('w'); __f.write(__aeJSON(__res)); __f.close();
}})();
"""
