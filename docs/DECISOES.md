# Decisões (rulings)

Formato: decisão — por quê — custo se estiver errada.

- Alvo é o AE **2027** (27.0.0). A pasta "Adobe After Effects 2026" só tem `Scripts/`, sem o app. — Era a única instalação completa. — Refazer as sondas noutra versão.
- REPO_DIR é o diretório atual; a linguagem é Python 3.11+ com o SDK oficial `mcp`. — Os placeholders do prompt vieram vazios; usei os padrões dele. — Baixo.
- Ghidra via `analyzeHeadless -noanalysis` com decompilação só dos endereços-alvo. — O provedor Ghidra do REA estourou o tempo (330 s) no AfterFXLib. — Funções não decompiladas podem esconder detalhes. O uso de nm/otool reduz esse risco.
- `evidencias.json` fica fora do git. — Contém tabelas de símbolos da Adobe (regra de sala limpa). — O revisor precisa regerar o arquivo localmente.
- O resultado volta por arquivo temporário, não pelo retorno do DoScript. — O DoScript só devolve o status (Fase 2, sondas 2 e 3). — Nenhum.
- O script vai como `argv` de um AppleScript fixo, e não escapado dentro do fonte AppleScript. — Elimina toda uma classe de injeção e de quebra por aspas. O prompt pedia escape para AppleScript, mas isto é estritamente mais seguro. — Nenhum conhecido.
- `override true` por padrão, com fila serial e espera do marcador após timeout. — Sem override, uma colisão abre um alerta modal que trava o AE até alguém clicar (sonda 12). — Pode interromper um script de terceiros em andamento. Dá para desligar com `AE_MCP_OVERRIDE=0`.
- O servidor não inicia o render, só enfileira. — `render()` bloqueia o AE e reproduz o cenário da sonda 12. — O usuário renderiza pelo AE ou pelo `aerender`.
- Não abrir o AE automaticamente. — A inicialização leva cerca de 60 s, e abrir o app é uma ação visível para o usuário. — O agente precisa pedir que o usuário abra o AE.
- `layer_type` usa `null_object` em vez de `null`. — O SDK MCP 2.x converte a string "null" em None antes da validação (avaliações t5 e t7). — Agentes que tentarem "null" recebem um erro de validação com a lista de valores.
- `ae_queue_render` recusa e desfaz o item quando o template de saída troca a extensão pedida. — O baseline da skill mostrou que .mov virava .mp4 em silêncio e deixava um item extra na fila. — Quem quer .mov precisa escolher um template QuickTime.
- Não há ferramenta para remover itens da fila de render nem para importar footage. — Fica fora do escopo pedido; `ae_run_extendscript` ou o usuário cobrem. — Um agente pode precisar pedir ajuda ao usuário.
