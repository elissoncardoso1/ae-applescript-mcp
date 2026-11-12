# Superfície de automação AppleScript — After Effects 2027

Alvo: `/Applications/Adobe After Effects 2027/Adobe After Effects 2027.app`, versão 27.0.0 (build 78), arm64.
Ambiente: macOS 27.2.1. Análise feita em 2026-11-12.

Legenda de confiança:
- **confirmado**: visto no código ou no recurso e observado em execução (Fase 2);
- **provável**: visto estaticamente, sem prova em execução;
- **hipótese**: inferido, sem prova direta.

## Onde a lógica vive

| Peça | Local | Como foi visto |
|---|---|---|
| Habilitação de scripting | `Contents/Info.plist`: `NSAppleScriptEnabled = Yes`, `OSAScriptingDefinition = ae.sdef` | REA `inspect_plist` (ev_8b0e86…) |
| Dicionário | `Contents/Resources/ae.sdef` (1.5 KB, inclui o Standard Suite do Cocoa por XInclude) | leitura direta; `sdef` falha sem Xcode |
| Classes dos comandos | `AfterFXLib.framework`: `AEDoScriptCommand` e `AEDoScriptFileCommand`, subclasses de `NSScriptCommand` | `nm -m` |
| Handler DoScript | `-[AEDoScriptCommand performDefaultImplementation]` @ `0xda0798` | `otool -tV` + Ghidra 12.1.4 headless (decompilação direcionada) |
| Handler DoScriptFile | `-[AEDoScriptFileCommand performDefaultImplementation]` @ `0xda1ce0` | `nm -m` + Ghidra |
| Registro do executor | `CEggApp::InstallScriptHandler(DoScriptHandler*)` @ `0x655318` grava o ponteiro em `gEgg+0x2c0` | Ghidra |
| Executor ExtendScript e mensagens de erro | `Plug-ins/Keyframe/Scripting.plugin` (63 MB) | `strings`; IDs `$$$/AE/Scripting/LStr/00xx` |
| Assinatura | AfterFXLib assinado por Developer ID Adobe (JQ525L2MZD), hardened runtime | REA `inspect_signature` (ev_7201991f…) |

Fluxo do `DoScript`, conforme a decompilação (com minhas palavras):
1. lê o parâmetro direto (texto) e o argumento `override` (booleano);
2. se `gEgg+0x2c0` for nulo (plugin de scripting não carregado), registra o erro `ScriptingNotLoaded` e devolve 1;
3. copia o texto como UTF-16 (`CFStringGetCharacters`), então qualquer Unicode chega intacto;
4. chama o executor pela primeira entrada da vtable com (script, override, 0, 0) e recebe um **inteiro**;
5. registra no trace interno "DoScript result = <int>" e devolve esse inteiro como texto.

## Tabela de superfície

| Comando | Parâmetros | Retorno | Erros conhecidos | Fonte | Confiança |
|---|---|---|---|---|---|
| `DoScript` (evento `misc`/`dosc`) | direto: texto ExtendScript; `override` (`Over`, booleano, opcional) | texto com **status inteiro**: `"0"` = executou sem exceção, `"1"` = falhou ou foi recusado. **Não** devolve o valor do script | -1712 (timeout do Apple Event; o script continua rodando no AE); -1743 (Automação negada pelo TCC, esperado); retorno `"1"` em erro de sintaxe, exceção não tratada, plugin ausente ou segundo script concorrente | sdef; `0xda0798`; Fase 2 | **confirmado** |
| `DoScriptFile` (`misc`/`file`) | direto: arquivo (`POSIX file`); `override` | texto (status) | arquivo inexistente devolve `"0"` sem aviso (falha silenciosa) | sdef; `0xda1ce0`; Fase 2 | **confirmado** (só o caso de arquivo inexistente) |
| `override true` | — | — | permite executar enquanto outro script roda; sem ele, o AE recusa e abre **alerta modal** (LStr/0050) | Scripting.plugin LStr/0049–0050; Fase 2 | **confirmado** |
| Standard Suite (`quit`, `open`, `count windows`…) | conforme CocoaStandard.sdef | variado | `quit` devolve -128 enquanto há alerta modal/estado de script preso | ae.sdef (XInclude); Fase 2 | **confirmado** só para `quit`; o resto é **provável** |
| Acesso a arquivo/rede dentro do DoScript | — | — | escrita de arquivo funcionou com a preferência `Pref_SCRIPTING_FILE_NETWORK_SECURITY` = 0 (desligada) | símbolo `ScriptingAllowFileAndNetworkAccessScoper` no caminho de unwind do handler (`0xda0f6c`); Fase 2 | **confirmado** (escrita local); rede: **hipótese** |
| Diálogo modal nativo bloqueia scripts | — | — | mensagem LStr/0044 ("não é possível rodar script com diálogo modal aguardando") | Scripting.plugin | **provável** (testado só com o alerta de script concorrente, ver validacao.md) |
| Scripts não alteram preferências de segurança | — | — | LStr/0031 | Scripting.plugin | **provável** |
| Erros de chamada ExtendScript | — | — | mensagens "Unable to call … because of parameter N" (LStr/0003), "Value out of range" (0007/0008), "Path is not valid" (0010), restrições de render (0029, 0032–0036, 0053–0057) | Scripting.plugin | **confirmado** para LStr/0003 (via try/catch); demais **provável** |

## Lacunas registradas (REA `record_unknown`)

1. Formato do texto de retorno → **resolvida na Fase 2**: é o status inteiro.
2. DoScript libera arquivo/rede sem a preferência? → **resolvida para escrita local**; rede não testada.
3. Erro recebido com diálogo modal / reentrância → **parcialmente resolvida**: reentrância sem override devolve `"1"` e abre alerta modal; modal nativo não testado.

## Limites desta análise

- O provedor Ghidra do REA estourou o tempo (330 s) ao analisar o AfterFXLib inteiro. Contornei com `analyzeHeadless -noanalysis` e um script próprio que decompila só os endereços-alvo (`docs/recon/ghidra/DecompTargets.java`).
- `sdef` exige Xcode completo; li o `.sdef` do bundle diretamente.
- `evidencias.json` (2.5 MB) contém tabelas de símbolos do binário da Adobe; fica em disco e fora do git (regra de sala limpa).
