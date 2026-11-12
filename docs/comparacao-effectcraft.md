# ae-applescript-mcp × EffectCraft MCP

Fontes:
- **ae-applescript-mcp:** código, testes e avaliações deste repositório (AE 27.0.0).
- **EffectCraft 0.17.0:** a skill `effectcraft-motion` (afirmações verificadas no laboratório dela) e a lista de tools MCP exposta nesta máquina. **Não re-testei o EffectCraft para esta comparação.**

## Em uma frase

- **ae-applescript-mcp** dirige o **Adobe After Effects de verdade**: a saída é um `.aep` real, o render tem fidelidade de 100% e todos os plug-ins instalados funcionam. A superfície é estreita (13 ferramentas), e o agente não vê nem renderiza nada.
- **EffectCraft** é um **compositor próprio, no estilo AE**. A superfície é enorme (734 comandos e 307 efeitos), há preview com imagem, render e Lottie, e ele roda sem interface. Em troca, não abre `.aep`, não roda plug-ins da Adobe e a fidelidade ao AE não é garantida.

## Tabela

| Dimensão | ae-applescript-mcp | EffectCraft MCP |
|---|---|---|
| Programa controlado | Adobe After Effects (licença Adobe) | EffectCraft, open source em Rust, alpha 0.17 |
| Transporte | osascript → Apple Event `DoScript` → ExtendScript → arquivo JSON | JSON-RPC stdio nativo; headless em processo ou `--bridge` para o app aberto |
| Precisa do app aberto | **sim**; o usuário abre (cerca de 60 s) | não (headless); o bridge é opcional |
| Plataforma | só macOS | macOS (mais testado), Linux, Windows |
| Latência | cerca de 110 ms por chamada + script, um por vez | em processo, sem Apple Events |
| Nº de ferramentas | 13 consolidadas (`ae_*`) | 27 tools (+9 no bridge), dando acesso a **734 comandos** |
| Filosofia | poucas ferramentas de alto nível, lote por chamada | genéricas (`command_run`, `get/set_property`) + catálogo |
| Leitura do projeto | overview (até 50 itens), inspect da comp (até 100 camadas, 20 keys por propriedade, parâmetros de efeito) | `get_project`, `get_comp`, `get_layer` (árvore completa com `path`), `get_property` (valor no tempo, keys) |
| Tipos de camada | texto, sólido, null, ajuste, retângulo, elipse | todos os do engine (texto, sólido, shape com path/estrela/trim/repeater, câmera, precomp…) |
| Propriedades | transform, texto, tempos, pai, âncora, caminho genérico | qualquer `path` da árvore |
| Keyframes | lote; easing `linear`, `ease` ou `hold` por trilha | lote; `linear`, `bezier`, `hold` ou `easyEase`; velocity e influence pelos comandos `keys.*` |
| Expressões | não (só pela válvula de escape) | `set_property {expression}` + `expr.errors` |
| Efeitos | **qualquer efeito instalado no AE, inclusive de terceiros** (Trapcode, Element…) | 307 nativos; **plug-ins do AE não rodam** |
| Presets | os do AE (só pela válvula de escape) | 54 próprios (contra 621 do AE) |
| Ver o resultado | **não**; a verificação é por dados (`ae_inspect_comp`) | **`render_frame` devolve PNG inline** |
| Render final | **só enfileira**; o usuário clica em Render no AE ou usa `aerender` | renderiza: H.264, ProRes 4444 com alpha, WebM VP9 com alpha, GIF, PNG, HEVC/AV1/EXR… |
| Lottie | não | sim, com `warnings` (só 5 efeitos exportam) |
| Formato de projeto | **.aep** nativo: o pipeline Adobe e o cliente abrem direto | **.ecproj**; não abre `.aep`, `.aepx`, `.mogrt` nem `.ffx` |
| Fidelidade visual | é o próprio AE | medida só para ease escalar; "sempre olhe os frames" |
| Desfazer | undo group nomeado por chamada (Cmd+Z no AE); sem ferramenta de undo | `undo`, `redo`, `history` com ramos; `batch` atômico com rollback |
| Atomicidade em lote | parcial: um erro no meio do lote deixa os passos anteriores (dá para desfazer com 1 Cmd+Z) | `batch {atomic}`: falhou, desfaz tudo; `$1.layer` reaproveita resultados |
| Código livre | `ae_run_extendscript`, **desligado por padrão** (variável de ambiente) | `run_script` e `execute_command` sempre disponíveis; confináveis com `--automation-*-root` |
| Proteção de dados | recusa descartar alterações não salvas, sobrescrever `.aep` ou render, e apagar sem pedido explícito | o render **sobrescreve sem perguntar**; o CLI sem `--project` abre o demo; trabalho headless só em memória sem `--autosave` |
| Validação de entrada | Pydantic + mensagem com exemplo | chave desconhecida dá erro com a lista; **tipo errado é ignorado sem aviso** (ex.: `width:"wide"` vira 1920) |
| Falhas de ambiente | AE fechado, Automação (-1743), diálogo modal, timeout: mensagens dedicadas e `doctor.sh` | não há diálogos no headless; no bridge, `ui_*` |
| Custo | assinatura Adobe | gratuito |
| Maturidade | v0.1; 51 testes, 11/11 avaliações, skill testada com agentes | 0.17 alpha; bugs abertos em grupos de shape, CJK e cor do ProRes |

## Quando usar cada um

| Situação | Escolha |
|---|---|
| Entregar `.aep` ao cliente, editor ou equipe que usa Adobe | **ae-applescript-mcp** |
| O projeto do usuário já existe em `.aep` | **ae-applescript-mcp** (o EffectCraft não abre) |
| Precisa de plug-in de terceiros ou fidelidade exata do AE | **ae-applescript-mcp** |
| O agente deve iterar sozinho **vendo** os frames | **EffectCraft** (`render_frame`) |
| Entregar o vídeo renderizado, com alpha, ou em Lottie, sem intervenção | **EffectCraft** |
| Sem licença Adobe, em CI ou servidor, Linux ou Windows | **EffectCraft** |
| Expressões, máscaras, câmeras, precomps, shapes complexos | **EffectCraft**, ou o AE via `ae_run_extendscript` habilitado |
| Lotes de variações (troca de texto em N versões) | os dois; o EffectCraft é mais rápido (CLI `run --args-file`) |

Não há ponte entre eles: o EffectCraft não lê `.aep`, e o AE não lê `.ecproj`. Para começar num e terminar no outro, é preciso refazer a peça por comandos.

## O que o EffectCraft tem e daria para trazer ao ae-applescript-mcp

| Recurso | Viabilidade no AE via DoScript | Status |
|---|---|---|
| Preview de frame com imagem | `CompItem.saveFrameToPng(time, file)` existe no scripting do AE | **hipótese**, não testado |
| Expressões | `property.expression = "…"` + leitura de `expressionError` | provável |
| Lote atômico | executar e chamar `app.executeCommand(undo)` em caso de erro | hipótese |
| Leitura genérica de propriedade | `__prop(path)` já existe internamente | fácil |
| Render dentro do servidor | inviável sem travar o AE (`render()` bloqueia); `aerender` via subprocess seria a alternativa | a avaliar |
