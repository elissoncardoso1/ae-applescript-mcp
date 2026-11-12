# Limitações conhecidas

Baseadas no que foi observado na Fase 2 (`docs/recon/validacao.md`) e nas avaliações.

## Do transporte (AppleScript/DoScript)

- **O DoScript não devolve valores**, só o status `0`/`1`. Todo resultado passa por um arquivo temporário. Se o AE recusar o script (alerta aberto), não há arquivo, e a mensagem é genérica ("recusou o script").
- **Um script por vez.** O AE não executa scripts em paralelo; o servidor serializa. Cada chamada custa cerca de 110 ms mais o tempo do script.
- **Timeout não cancela.** Após -1712, o script continua no AE. O servidor espera ele terminar antes de enviar outro e, enquanto isso, responde "ainda processando".
- **Diálogos modais travam tudo.** Se houver um alerta ou diálogo aberto no AE (fontes ausentes ao abrir projeto, preferências, um `alert()`), os scripts falham até o usuário fechá-lo. O servidor não clica em diálogos: isso exigiria a permissão de Acessibilidade.
- **AE fechado.** O servidor não abre o app; o usuário precisa abri-lo (a inicialização leva cerca de 60 s).
- **Tamanho do script.** O script vai como argumento de processo. 500 KB funcionou; o limite do macOS (`ARG_MAX`, ~1 MB) vale para `ae_run_extendscript`.
- `DoScriptFile` com arquivo inexistente devolve sucesso silencioso; por isso não é usado.
- Só macOS. No Windows, o AE não expõe esse dicionário AppleScript.

## Do ExtendScript e das ferramentas

- **Render não é iniciado.** `renderQueue.render()` bloqueia o AE dentro do script e recriaria o cenário de alerta modal. O usuário renderiza pelo AE ou pelo `aerender`.
- **Sem previews e screenshots.** O agente verifica o resultado lendo dados (`ae_inspect_comp`), não imagens.
- **Nomes de efeitos e propriedades.** Nomes exibidos dependem do idioma da interface do AE; os matchNames (`ADBE Gaussian Blur 2`) são estáveis. A avaliação rodou com o AE em inglês.
- **Texto.** `addText` cria a âncora na linha de base; para centralizar, use `justification='center'` + `center_anchor=true`. A fonte precisa ser o nome PostScript.
- **Keyframes.** O easing é uniforme por trilha (`linear`, `ease` ou `hold`); não há curvas bezier personalizadas nem easing espacial. `replace_existing` apaga os keyframes anteriores da propriedade.
- **Leitura truncada.** O overview lista até 50 itens, o inspect até 100 camadas e até 20 keyframes por propriedade.
- **Pré-parse de argumentos do SDK MCP 2.x.** Strings que parecem JSON (`"null"`, `"3"`, `"true"`) podem ser convertidas antes da validação em campos que não são `str`. Por isso o tipo de camada é `null_object`, e um valor de keyframe `"1.0"` vira `1`.
- **Erros de validação** de tipo e intervalo vêm do Pydantic, com o texto padrão do SDK (sem stack trace).

## Não testado

- Comportamento com um diálogo modal **nativo** do AE (ex.: Preferências aberto). A mensagem LStr/0044 indica bloqueio, mas o comportamento não foi observado.
- Acesso à rede a partir do DoScript.
- Outras versões do AE (2025/2026).
