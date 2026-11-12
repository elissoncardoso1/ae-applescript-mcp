# Design — ae-applescript-mcp

## Transporte

```
cliente MCP ──stdio──▶ servidor Python (MCPServer, mcp 2.x)
                          │  lock global (fila serial)
                          ▼
                 osascript - <script.jsx> <override> <timeout>     (AppleScript fixo, lido do stdin)
                          │  tell application "<AE_APP_PATH>" to DoScript (item 1 of argv) override …
                          ▼
                 After Effects → ExtendScript (template fixo + argumentos JSON)
                          │  grava {ok, data | error} em JSON UTF-8
                          ▼
                 arquivo de resultado exclusivo (tempdir do servidor) ──▶ servidor lê e apaga
```

- **AppleScript fixo.** O único texto variável no fonte é o caminho do app, que vem da configuração e é escapado. O ExtendScript vai como `argv`, então nunca se interpola nada no AppleScript.
- **ExtendScript = prelúdio + template fixo da ferramenta.** Os argumentos entram como **um** literal JSON (`json.dumps(..., ensure_ascii=True)`), que também é um literal de objeto válido em ES3. Nenhum valor do usuário é concatenado ao código.
- **Retorno.** O `DoScript` só devolve o status (Fase 2). O valor vem pelo arquivo, serializado por `__aeJSON`, um serializador ES3 próprio (o ExtendScript não tem `JSON`).
- **Fila serial.** Um `threading.Lock`. Em timeout (-1712), o servidor guarda o caminho do arquivo pendente. A chamada seguinte espera esse arquivo aparecer (até `AE_MCP_TIMEOUT` s) antes de enviar. Se ele não aparecer, a chamada falha com uma instrução clara e nada é enviado.
- **override.** Fica ligado por padrão (`AE_MCP_OVERRIDE=1`); veja `docs/DECISOES.md`.
- **Undo.** Toda ferramenta de escrita roda entre `app.beginUndoGroup("MCP: <ação>")` e `endUndoGroup()` (este num `finally`).

## Configuração (variáveis de ambiente)

| Variável | Padrão | Efeito |
|---|---|---|
| `AE_APP_PATH` | `/Applications/Adobe After Effects 2027/Adobe After Effects 2027.app` | app alvo |
| `AE_MCP_TIMEOUT` | `60` | segundos por chamada |
| `AE_MCP_OVERRIDE` | `1` | parâmetro `override` do DoScript |
| `AE_MCP_ENABLE_RUN_EXTENDSCRIPT` | `0` | habilita `ae_run_extendscript` |

## Modelo de erros

Cada falha vira `ToolError` com o texto: **o que houve + como corrigir + exemplo válido**. Nunca há stack trace.

| Situação | Detecção | Mensagem (resumo) |
|---|---|---|
| AE fechado | o AppleScript devolve `AE_NOT_RUNNING` | "Abra o After Effects e espere a tela inicial; depois repita." |
| Automação negada | erro -1743 | "Ajustes do Sistema › Privacidade e Segurança › Automação: permita que <app cliente> controle o After Effects." |
| Timeout | -1712 | "O AE ainda está processando; a próxima chamada espera. Aumente AE_MCP_TIMEOUT se for comum." |
| Script recusado | stdout `1` e nenhum arquivo | "O AE recusou o script: provavelmente há um diálogo aberto ou outro script rodando. Feche os diálogos no AE." |
| Diálogo/cancelado | -128 | igual ao anterior |
| Erro ExtendScript | `{ok:false}` | a mensagem do AE, mais a dica do template e um exemplo |
| Validação de entrada | Pydantic / template | o campo e um exemplo válido |

## Ferramentas (13)

Todas aceitam o alvo por `comp_name` **ou** `comp_index` (base 1, a ordem do painel Projeto). Camadas são indicadas por `layer_index` (base 1, como no AE).
As de leitura aceitam `response_format: "concise" | "detailed"`.

| Ferramenta | Função | readOnly | destructive | idempotent |
|---|---|---|---|---|
| `ae_get_project_overview` | app, versão, arquivo do projeto, `dirty`, itens (até 50, com aviso), fila de render | ✔ | – | ✔ |
| `ae_inspect_comp` | configurações da comp e camadas (até 100): tipo, tempos, transform, texto, efeitos, propriedades com keyframes | ✔ | – | ✔ |
| `ae_create_comp` | cria uma comp (nome, largura, altura, duração, fps, cor de fundo) | ✘ | ✘ | ✘ |
| `ae_add_layer` | `text`, `solid`, `null`, `adjustment`, `shape_rectangle`, `shape_ellipse` | ✘ | ✘ | ✘ |
| `ae_set_layer_properties` | lote: nome, transform, in/out, opacidade, texto, fonte, tamanho, cor, justificação, pai, centralizar âncora, caminhos genéricos | ✘ | ✘ | ✔ |
| `ae_set_keyframes` | lote: propriedade + lista de `{time, value}` e easing `linear\|ease\|hold` | ✘ | ✘ | ✔ |
| `ae_apply_effect` | adiciona um efeito (matchName ou nome exibido) e define parâmetros | ✘ | ✘ | ✘ |
| `ae_remove_layers` | apaga camadas por índice | ✘ | ✔ | ✘ |
| `ae_queue_render` | adiciona a comp à fila de render com caminho de saída. **Não renderiza.** | ✘ | ✘ | ✘ |
| `ae_new_project` | novo projeto; recusa se houver alterações não salvas, a menos que `discard_unsaved_changes=true` | ✘ | ✔ | ✘ |
| `ae_open_project` | abre um `.aep`, com a mesma proteção | ✘ | ✔ | ✘ |
| `ae_save_project_as` | salva em `.aep`; recusa sobrescrever sem `overwrite=true` | ✘ | ✔ | ✔ |
| `ae_run_extendscript` | executa código arbitrário; **desligada por padrão** | ✘ | ✔ | ✘ |

`ae_remove_layers` entrou além da lista do prompt: sem ela, desfazer um passo errado exigiria a válvula de escape.

### Contratos (resumo; o schema completo está em docs/TOOLS.md)

- **ae_create_comp**: `name`, `width` (4–30000), `height`, `duration` (s, >0), `frame_rate` (padrão 30), `background_color` (`#RRGGBB`). Devolve `{comp_index, name, width, height, duration, frame_rate}`.
- **ae_add_layer**: `comp_*`, `layer_type`, `name?`, `text?` (obrigatório para `text`), `color?`, `width?/height?` (para solid e shape; padrão = tamanho da comp), `position?` `[x,y]`. Devolve `{layer_index, name, type}`.
- **ae_set_layer_properties**: `comp_*`, `changes: [{layer_index, name?, position?, scale?, rotation?, opacity?, anchor_point?, in_point?, out_point?, text?, font?, font_size?, fill_color?, justification?, parent_index?, center_anchor?, properties?: {"Caminho/Da/Prop": valor}}]`. Se a propriedade tiver keyframes, o erro manda usar `ae_set_keyframes`.
- **ae_set_keyframes**: `comp_*`, `tracks: [{layer_index, property, keyframes: [{time, value}], easing}]`. `property` aceita os atalhos `position|scale|rotation|opacity|anchor_point` ou um caminho como `Effects/Gaussian Blur/Blurriness`.
- **ae_apply_effect**: `comp_*`, `layer_index`, `effect`, `params?: {nome: valor}`. Devolve o nome do efeito e a lista de parâmetros disponíveis.
- **ae_queue_render**: `comp_*`, `output_path` (absoluto; a pasta precisa existir), `output_module_template?`, `render_settings_template?`, `overwrite=false`. Devolve `{rq_index, status, output}`.
- **ae_save_project_as**: `path` (.aep, absoluto), `overwrite=false`.
- **ae_new_project / ae_open_project**: `discard_unsaved_changes=false`; `ae_open_project` também recebe `path`.
- **ae_run_extendscript**: `code` é o corpo de uma função; o `return` é serializado. Erros de sintaxe são capturados porque o código passa por `eval`.

## Saída

- Por padrão, JSON compacto, com nomes legíveis (nome da comp ou camada, tipo).
- Listas truncadas trazem `truncated: true` e um `hint` de como refinar a busca (ex.: "use ae_inspect_comp com comp_name").
