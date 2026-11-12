# Fase 2 — Validação empírica

Todas as sondas rodaram com `osascript` contra o AE 27.0.0, com um projeto vazio e não salvo.
O Terminal já tinha permissão de Automação para o AE (nenhum prompt do TCC apareceu).

| # | Sonda | Resultado observado |
|---|---|---|
| 1 | AE fechado: `application id "com.adobe.AfterEffects.application" is running` | `false` em 50 ms, sem abrir o app. Um `tell` direto **abriria** o AE (a inicialização levou ~56 s). |
| 2 | `DoScript "app.version"`, `"1+2"`, `"'abc'"` | sempre `"0"`. O valor do script **não volta**. |
| 3 | Canal por arquivo: o script grava em `File(...)` com `encoding='UTF-8'` | funcionou: `27.0x78`, `numItems=0`. A preferência de segurança de arquivo/rede estava em 0. |
| 4 | Latência de um `DoScript "1"` | 100–120 ms por chamada (5 medições). |
| 5 | UTF-8: `"Clínica TAAL — 10 anos ação 日本 🎬"`, script passado como `argv` de um AppleScript fixo | ida e volta idênticas, `length` = 33 (o emoji ocupa 2 unidades UTF-16). |
| 6 | Script de 500 KB via `argv` | executou em 0,19 s. |
| 7 | Erro de sintaxe sem try/catch | retorno `"1"`, sem mensagem e sem diálogo. |
| 8 | `throw new Error()` sem try/catch | retorno `"1"`, sem diálogo. |
| 9 | Erro de sintaxe via `eval` dentro de try/catch | `SyntaxError: Expected: ;`, `line=1`, gravado no arquivo. |
| 10 | `app.project.item(99)` num projeto vazio, com try/catch | `Error: After Effects error: Unable to call "item" because of parameter 1. The range has no values.` |
| 11 | Timeout: `with timeout of 2 seconds` para um script de 4 s | osascript falha com **-1712** após 2 s; o script **continua** e termina no AE. |
| 12 | Concorrência: script A (`$.sleep(6000)`), script B enviado 1 s depois, sem override | B é recusado e o AE abre um **alerta modal** (LStr/0050). A congela até alguém clicar em OK. Enquanto o alerta está aberto, todo DoScript sem override devolve `"1"` e `quit` devolve -128. Com `override true`, o script roda normalmente. Depois do OK, A terminou. |
| 13 | `DoScriptFile` com arquivo inexistente | `"0"` — falha silenciosa. |
| 14 | AE ocupado renderizando | **não testado diretamente.** Como `renderQueue.render()` bloqueia dentro do script, a situação é a do item 12. Decisão: o servidor só enfileira; não inicia o render. |

## Consequências de design

1. O resultado volta por arquivo temporário: cada chamada grava um JSON num arquivo exclusivo, criado pelo servidor.
2. O ExtendScript chega como `argv` de um AppleScript fixo. Não há interpolação no fonte AppleScript, então não é preciso escapar nada para AppleScript.
3. Fila serial no servidor. Após um timeout, o servidor espera o arquivo de resultado (marcador de conclusão) antes de liberar a fila. Assim nunca envia um segundo script enquanto o anterior roda, o que evitaria o alerta modal.
4. `override true` por padrão: se um script de terceiros estiver rodando, o nosso entra em vez de abrir o alerta modal. Pode ser desligado com `AE_MCP_OVERRIDE=0`.
5. Todo template roda dentro de try/catch e devolve `{ok:false, error:{...}}`. O retorno `"1"` sem arquivo vira "o AE recusou o script" (provável alerta ou script concorrente).
6. Não abrir o AE automaticamente. Se ele estiver fechado, o erro manda abri-lo.
