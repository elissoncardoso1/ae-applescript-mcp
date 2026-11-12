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

## Revisão final (revisor independente)

- Final: corrigido REMOVE_LAYERS com índices duplicados ([2,2] apagava B e C). — `test_remove_layers_ignores_duplicate_indexes` RED→GREEN.
- Final: corrigido `replace_existing` como padrão destrutivo. Agora o padrão é `false`, e o easing só se aplica aos keyframes novos. — `test_set_keyframes_keeps_user_keys_by_default_and_eases_only_new_ones` RED→GREEN.
- Final: corrigida a contagem de KeyframeEase (2D=2, 3D=3, demais=1, segundo o guia de scripting). — `test_color_ease_uses_single_keyframe_ease` RED→GREEN.
- Final: corrigido o pendente que travava o servidor para sempre. Ele agora expira com aviso; o timeout avisa que a operação pode ter sido aplicada. — `test_stale_pending_is_cleared_after_wait_expires` e `test_timeout_message_warns_operation_may_have_applied` RED→GREEN.
- Final: lock entre processos (`fcntl.flock` em `$TMPDIR/ae-applescript-mcp.lock`). — `test_lock_is_shared_across_processes` RED→GREEN.
- Final: o inspect não quebra em câmeras e luzes (`__pv` devolve null quando a propriedade não existe). — Coberto pelo teste de compilação; comportamento com câmera real não testado.
- Final: arquivo de resultado corrompido vira AEError, e o arquivo é sempre apagado. — `test_corrupt_result_file_becomes_aeerror` RED→GREEN.
- Final: testes de templates no Node (compilação ES3 de todos, recusa de projeto sujo, literal ASCII) e mapeamento de erros do osascript.
- Final: Ruling — o pendente continua sendo por processo (só o lock é compartilhado). — Um timeout num processo não bloqueia outro, e o flock já impede a colisão real. — Se dois clientes usarem o AE ao mesmo tempo e um der timeout, o outro pode enviar enquanto o script lento termina, o que intercala com override.
- Final: minor (deferred): `__prop` divide por "/", então efeitos como "Hue/Saturation" exigem matchName.
- Final: minor (deferred): OPEN_PROJECT ignora o retorno de `app.open`.
- Final: minor (deferred): APPLY_EFFECT deixa o efeito quando um parâmetro é inválido (a mensagem avisa).
- Final: minor (deferred): `mkdtemp` do runner não é removido ao sair.
- Final: minor (deferred): janela mínima entre `__f.open` e `close` na detecção do pendente.
- Final: minor (deferred): os vetores de LayerChange não têm limite de tamanho.
- Final: minor (deferred): anotações de `ae_queue_render` com overwrite e de `ae_set_keyframes` com replace_existing não são destrutivas.
- Final: minor (deferred): precomp é classificada como "footage" e `__hex` falha com cores HDR acima de 1.0.
- Final: minor (deferred): helpers ficam globais no engine do AE.
- Final: minor (deferred): doctor.sh interpola `$APP` no AppleScript; em -1712, o arquivo é gravado depois do `rm`.
- Final: minor (deferred): o guard dos evals e da integração roda uma vez só e usa `startswith` sem separador.
- Final: minor (deferred): suspeitas não confirmadas no AE: inPoint antes de outPoint ao mover camadas para frente; inspect detailed lento em comps pesadas; trocar texto apaga estilos por caractere.
