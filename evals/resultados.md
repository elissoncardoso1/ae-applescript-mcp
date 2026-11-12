# Resultados das avaliações (Fase 5)

Execução: `uv run python evals/run_evals.py`, com o AE 27.0.0 aberto. Cliente MCP stdio real (`mcp` 2.3.0). Cada tarefa começa num projeto vazio e é verificada lendo o projeto de volta (`ae_inspect_comp` / `ae_get_project_overview`).

| Tarefa | O que verifica | 1ª rodada | Após ajuste |
|---|---|---|---|
| t1_taal | comp 1080x1920 de 10 s, texto "Clínica TAAL — 10 anos" centralizado, fade-in de 1 s com ease, render enfileirado | ok | ok |
| t2_lower_third | barra + nome entrando da esquerda (keyframes de posição com ease) | ok | ok |
| t3_pulse | elipse, escala 100→120→100 | ok | ok |
| t4_effects | sólido + Gaussian Blur (25) + Fill (#F05378) | ok | ok |
| t5_parent | null controlador, 2 filhos, rotação 0→360 | **falhou** | ok |
| t6_sequence | 3 textos com in/out em sequência | ok | ok |
| t7_cleanup | cria 4 camadas, remove 2, renomeia | **falhou** | ok |
| t8_countdown | Source Text 3-2-1 com keyframes hold | ok | ok |
| t9_save_reopen | salva .aep temporário, reabre e confere | ok | ok |
| t10_recover | erro guiado: comp inexistente → mensagem aponta overview → corrige | ok | ok |
| t11_adjustment | camada de ajuste com Glow entre 2 e 4 s | ok | ok |

**Taxa de sucesso: 9/11 (82%) na 1ª rodada → 11/11 (100%) após o ajuste.**

## Ajustes feitos a partir das falhas

1. **`layer_type="null"` chegava como `None`** (t5, t7). O SDK MCP 2.x tenta interpretar como JSON os argumentos string destinados a campos que não são `str`. A string `"null"` virou `None`, e o Literal recusou. Correção: o valor passou a ser `null_object` (na entrada e no tipo devolvido pelo inspect). Teste de regressão: `tests/test_protocol.py::test_every_layer_type_survives_argument_parsing`, que roda pelo protocolo e falhou antes da correção.

## Observações para a skill e as limitações

- Uma camada nova entra em `layer_index` 1 e empurra as outras para baixo. As tarefas t2 e t5 dependem disso; a skill precisa deixar isso claro.
- O valor de keyframe `"3"` pode virar o número 3 pelo mesmo pré-parse. Para Source Text isso não importa (o template converte com `String`), mas `"1.0"` viraria `"1"`.

## Teste da skill (Fase 7)

| Rodada | Agente | Tarefas | Resultado (verificado por mim lendo o projeto) | O que mudou depois |
|---|---|---|---|---|
| RED (sem skill) | só o harness e `list` | "Story": texto centralizado, fade in/out, fundo, render .mov | requisitos atendidos, mas com 2 itens na fila de render (.mp4 indesejado) e adivinhações | **servidor:** `ae_queue_render` passou a recusar a troca silenciosa de extensão; `color` agora pinta o texto; inspect mostra a cor do sólido. **skill:** ordem das camadas, `comp_name` em vez de índice, último frame, tamanho da fonte |
| GREEN (com skill) | só a SKILL.md | A (TAAL 10 anos + render), B (blur animado + Fill), C (3 palavras em sequência) | **3/3**, sem nenhum erro de ferramenta | **servidor:** o inspect detailed mostra os parâmetros dos efeitos e o tamanho do texto. **skill:** opacidade do Fill para "sobrepor/tingir", receita de sequência centralizada, separação de fade-in e fade-out, cor padrão do texto, /private/tmp |
| REFACTOR | só a SKILL.md revisada | "Abertura": tingido leve, texto grande que cabe, fade-out no último meio segundo | **1/1**, sem erros; Fill Opacity 0.3, texto com 1204 px de 1920 | escala "levemente/tingido/forte", alvo de largura do texto (70–90%), início do fade-out, campo estático vs `animated` |
