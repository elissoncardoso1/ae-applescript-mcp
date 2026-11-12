# ae-applescript-mcp

Servidor MCP que controla o **Adobe After Effects no macOS por AppleScript**, sem plugin, painel CEP/UXP ou extensão instalada no AE.

```
cliente MCP → servidor Python → osascript → DoScript (Apple Event) → ExtendScript no AE → resultado JSON em arquivo temporário
```

São 13 ferramentas `ae_*`: ler projeto e comps; criar comp; adicionar camadas de texto, sólido, null, ajuste e shapes; alterar propriedades e keyframes em lote; aplicar efeitos; remover camadas; enfileirar render; abrir, criar e salvar projeto. A referência completa está em [docs/TOOLS.md](docs/TOOLS.md).

## Requisitos

- macOS com o Adobe After Effects instalado. Validado no AE 2027 (27.0.0), macOS 27.2.
- Python 3.11+ e [uv](https://docs.astral.sh/uv/).
- O After Effects **aberto** quando as ferramentas forem chamadas. O servidor não abre o app.

## Instalação

```bash
git clone <este repositório> ae-applescript-mcp && cd ae-applescript-mcp
uv sync
```

## Permissões necessárias

1. **Automação (macOS).** Na primeira chamada, o macOS pergunta se o app que roda o servidor (Terminal, Claude Desktop, VS Code…) pode controlar o "Adobe After Effects". Responda **OK**. Se negou por engano, vá em *Ajustes do Sistema › Privacidade e Segurança › Automação* e ligue a chave do After Effects para esse app. Sem isso, as chamadas falham com -1743.
2. **After Effects.** Não precisa mudar nenhuma preferência. Na Fase 2 vimos que scripts enviados por `DoScript` gravam arquivos mesmo com *"Allow Scripts to Write Files and Access Network"* desligada, e o servidor só grava o resultado no próprio diretório temporário.

Diagnóstico rápido: `bash skills/after-effects-applescript/scripts/doctor.sh`.

## Configuração do cliente MCP

Claude Code:

```bash
claude mcp add after-effects -- uv run --directory /caminho/para/ae-applescript-mcp ae-applescript-mcp
```

JSON (Claude Desktop, Cursor e outros):

```json
{
  "mcpServers": {
    "after-effects": {
      "command": "uv",
      "args": ["run", "--directory", "/caminho/para/ae-applescript-mcp", "ae-applescript-mcp"],
      "env": { "AE_MCP_TIMEOUT": "60" }
    }
  }
}
```

| Variável | Padrão | Uso |
|---|---|---|
| `AE_APP_PATH` | `/Applications/Adobe After Effects 2027/Adobe After Effects 2027.app` | outra versão do AE |
| `AE_MCP_TIMEOUT` | `60` | segundos por chamada |
| `AE_MCP_OVERRIDE` | `1` | `override` do DoScript (veja docs/SEGURANCA.md) |
| `AE_MCP_ENABLE_RUN_EXTENDSCRIPT` | `0` | `1` habilita a ferramenta perigosa `ae_run_extendscript` |

## Testes

```bash
uv run pytest                                   # unitários (precisa de node para os testes ES3)
AE_MCP_INTEGRATION=1 uv run pytest              # + integração (AE aberto, sem trabalho não salvo)
uv run python evals/run_evals.py                # 11 tarefas ponta a ponta
```

Os testes de integração e as avaliações **se recusam a rodar** se o projeto aberto no AE tiver alterações não salvas ou for um arquivo fora do diretório temporário.

## Documentação

- [docs/design.md](docs/design.md): transporte, modelo de erros, contratos
- [docs/SEGURANCA.md](docs/SEGURANCA.md) · [docs/LIMITACOES.md](docs/LIMITACOES.md) · [docs/DECISOES.md](docs/DECISOES.md)
- [docs/recon/](docs/recon/): engenharia reversa (superfície AppleScript) e validação empírica
- [evals/resultados.md](evals/resultados.md)
- Skill para agentes: [skills/after-effects-applescript/](skills/after-effects-applescript/SKILL.md)
