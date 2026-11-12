# Segurança

## Modelo de ameaça

| Ativo | Ameaça | Mitigação |
|---|---|---|
| Projetos do usuário | um agente sobrescreve, fecha sem salvar ou apaga trabalho | `ae_save_project_as` recusa sobrescrever sem `overwrite=true`. `ae_new_project` e `ae_open_project` recusam descartar alterações sem `discard_unsaved_changes=true`. As descrições mandam pedir confirmação ao usuário. Toda escrita fica num undo group nomeado `MCP: …`, desfazível com Cmd+Z. |
| Máquina do usuário | execução de código arbitrário: o ExtendScript lê e grava arquivos e, via DoScript, ignora a preferência de segurança do AE | código livre só existe em `ae_run_extendscript`, **desligada por padrão**. As outras 12 ferramentas executam apenas templates fixos. |
| Integridade do script | injeção por aspas, acentos ou caracteres de controle nos argumentos | veja "Escape de argumentos" abaixo |
| Disponibilidade do AE | alerta modal que trava o app (colisão de scripts, sondagem 12 da Fase 2) | fila serial, espera do script pendente após timeout, `override` ligado |
| Saída | gravação de render em lugar indevido | `ae_queue_render` exige caminho absoluto numa pasta existente e recusa sobrescrever sem `overwrite=true`. O render nunca é iniciado pelo servidor. |

## Escape de argumentos (por que não há injeção)

1. **AppleScript.** O fonte é fixo e só interpola o caminho do app, que vem da configuração do operador e é escapado. O ExtendScript vai como **`argv`** (`item 1 of argv`); o osascript nunca o compila como AppleScript.
2. **ExtendScript.** O código é prelúdio fixo + template fixo. Os argumentos do usuário entram como **um único literal JSON** gerado por `json.dumps(..., ensure_ascii=True)`, que é ASCII puro e sem U+2028/U+2029 crus. O template só lê `args.campo` como dado. Testado em `tests/test_jsx.py::test_args_are_data_not_code` com a carga `'); throw 1; //"); app.quit(); (`.
3. **Retorno.** O serializador ES3 próprio escapa aspas, barras, controles e tudo fora do ASCII imprimível. O arquivo de resultado tem nome aleatório (UUID) num diretório privado (`mkdtemp`, modo 700) e é apagado após a leitura.

## A ferramenta perigosa

`ae_run_extendscript`:
- só funciona com `AE_MCP_ENABLE_RUN_EXTENDSCRIPT=1` na configuração do servidor; o agente não consegue ligá-la;
- é anotada `destructiveHint=true`;
- passa o código por `eval` dentro de try/catch, então um erro de sintaxe vira mensagem em vez de travar o AE;
- não a habilite em sessões com agentes ou entradas não confiáveis: o ExtendScript tem o mesmo poder do usuário sobre o sistema de arquivos.

## override

Com `AE_MCP_OVERRIDE=1` (padrão), um script nosso pode rodar enquanto outro script de terceiros executa no AE, em vez de o AE abrir um alerta modal bloqueante. O efeito colateral é intercalar a execução com esse script. Os nossos scripts são curtos e transacionais (undo group). Com `0`, uma colisão abre o alerta, e o usuário precisa clicar OK.

## O que o servidor nunca faz

- abrir ou fechar o After Effects;
- iniciar render;
- alterar preferências do AE ou do macOS (incluindo o TCC);
- instrumentar o processo do AE.
