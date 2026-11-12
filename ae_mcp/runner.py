"""Execução serial de ExtendScript no After Effects via osascript → DoScript."""
import fcntl
import json
import os
import subprocess
import tempfile
import threading
import time
import uuid

from .jsx import build_script

NOT_RUNNING = ("O After Effects não está aberto. Abra o After Effects, espere a tela inicial "
               "terminar de carregar e repita a chamada.")
TIMEOUT = ("O After Effects ainda está processando o script (passou do timeout). A operação continua "
           "no AE e pode ter sido aplicada: confira com ae_inspect_comp/ae_get_project_overview antes "
           "de repetir, para não duplicar. Se for comum, aumente AE_MCP_TIMEOUT.")
STALE = ("O script anterior que passou do timeout não terminou. O servidor parou de esperar por ele. "
         "Ele pode ter sido aplicado em parte: confira com ae_inspect_comp antes de repetir.")
REFUSED = ("O After Effects recusou o script: provavelmente há um diálogo/alerta aberto no AE "
           "ou outro script rodando. Feche os diálogos no After Effects e repita.")
DENIED = ("O macOS bloqueou o controle do After Effects. Em Ajustes do Sistema › Privacidade e "
          "Segurança › Automação, permita que o app que roda este servidor (Terminal, Claude, "
          "VS Code…) controle o 'Adobe After Effects'. Depois repita.")


def _osascript(argv: list[str], stdin: str, timeout: float) -> tuple[int, str, str]:
    try:
        p = subprocess.run(argv, input=stdin, capture_output=True, text=True, timeout=timeout + 15)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "osascript travou (-1712)"


class AEError(Exception):
    pass


class AERunner:
    def __init__(self, app_path: str, timeout: int = 60, override: bool = True,
                 exec_fn=_osascript, pending_wait: float | None = None,
                 lock_path: str = os.path.join(tempfile.gettempdir(), "ae-applescript-mcp.lock")):
        self.timeout, self.override, self._exec = timeout, override, exec_fn
        self.pending_wait = timeout if pending_wait is None else pending_wait
        app = app_path.replace("\\", "\\\\").replace('"', '\\"')
        # Fonte fixo: o ExtendScript chega como argv, nunca interpolado aqui.
        self.applescript = (
            "on run argv\n"
            f'  if not (application "{app}" is running) then return "AE_NOT_RUNNING"\n'
            "  with timeout of (item 3 of argv as integer) seconds\n"
            f'    tell application "{app}" to return DoScript (item 1 of argv) '
            'override ((item 2 of argv) is "1")\n'
            "  end timeout\n"
            "end run\n")
        self._dir = tempfile.mkdtemp(prefix="ae-mcp-")
        self._lock = threading.Lock()  # o AE executa um script por vez
        self._lock_path = lock_path  # flock: serializa também entre processos (vários clientes MCP)
        self._pending: str | None = None

    def _wait_pending(self):
        if not self._pending:
            return
        deadline = time.monotonic() + self.pending_wait
        while not os.path.exists(self._pending):
            if time.monotonic() > deadline:
                self._pending = None  # não prender o servidor para sempre (AE reiniciado, script morto)
                raise AEError(STALE)
            time.sleep(0.1)
        os.remove(self._pending)
        self._pending = None

    def run(self, template: str, args: dict, undo: str | None = None, helpers: str = ""):
        with self._lock, open(self._lock_path, "a") as lockf:
            fcntl.flock(lockf, fcntl.LOCK_EX)
            self._wait_pending()
            path = os.path.join(self._dir, uuid.uuid4().hex + ".json")
            script = build_script(template, args, path, undo, helpers)
            argv = ["osascript", "-", script, "1" if self.override else "0", str(self.timeout)]
            rc, out, err = self._exec(argv, self.applescript, self.timeout)
            out = out.strip()
            if out == "AE_NOT_RUNNING" or "(-600)" in err or "(-609)" in err:
                raise AEError(NOT_RUNNING)
            if rc != 0:
                if "-1712" in err:
                    self._pending = path
                    raise AEError(TIMEOUT)
                if "-1743" in err:
                    raise AEError(DENIED)
                if "(-128)" in err:
                    raise AEError(REFUSED)
                raise AEError("Falha ao falar com o After Effects: " + (err.strip().splitlines() or ["?"])[-1])
            if not os.path.exists(path):
                raise AEError(REFUSED)
            try:
                with open(path, encoding="utf-8") as f:
                    res = json.load(f)
            except (OSError, ValueError):
                raise AEError("O resultado do After Effects veio incompleto. Confira o estado com "
                              "ae_inspect_comp antes de repetir.") from None
            finally:
                if os.path.exists(path):
                    os.remove(path)
            if not res.get("ok"):
                raise AEError("After Effects: " + res["error"]["message"])
            return res.get("data")
