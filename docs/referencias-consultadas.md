# Referências consultadas (sala limpa)

Regra seguida: ler só descrições, READMEs e listas de recursos; não abrir nenhum arquivo-fonte.
Em 2026-11-12, as páginas de listagem devolveram HTTP 403 ao fetch. Só foram lidos os resumos dos resultados de busca.

| Projeto | URL | O que foi lido | O que decidi fazer diferente |
|---|---|---|---|
| dakkshin/after-effects-mcp | https://awesome.ecosyste.ms/projects/github.com%2Fdakkshin%2Fafter-effects-mcp | resumo da busca: controle de comps, texto, shapes, solids e propriedades via ExtendScript; originalmente voltado ao Windows | sem painel dentro do AE; o transporte é Apple Events (DoScript) e o resultado volta por arquivo de uso único; só macOS |
| TheLlamainator/after-effects-mcp | https://mcpservers.org/servers/thellamainator/after-effects-mcp | resumo da busca: fork do anterior com efeitos, keyframes e easing; usa um "bridge panel" dentro do AE | nenhuma extensão ou painel instalado; keyframes e propriedades em lote numa única chamada |
| p10q/ae-mcp | https://mcpservers.org/vi/servers/p10q/ae-mcp | resumo da busca: ponte por arquivo com extensão CEP; AE 2022+ | nenhum CEP; nenhum polling de pasta pelo AE, que só executa o que recebe por Apple Event |
| JUNKDOGE-JOE/ae-mcp | https://glama.ai/mcp/servers/JUNKDOGE-JOE/after-effects-mcp | resumo da busca: estado do projeto, execução, previews, checkpoints | sem screenshots e previews nesta versão (fora do que o DoScript provou); undo groups nomeados em vez de checkpoints |

Documentação oficial usada: SDK MCP para Python 2.x (via Context7): `MCPServer`, `ToolAnnotations` e `ToolError`.
