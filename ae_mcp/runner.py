"""Execução serial de ExtendScript no After Effects via osascript → DoScript."""
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
TIMEOUT = ("O After Effects ainda está processando um script anterior (passou do timeout). "
           "Espere alguns segundos e repita; se for comum, aumente AE_MCP_TIMEOUT.")
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
                 exec_fn=_osascript, pending_wait: float | None = None):
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
        self._pending: str | None = None

    def _wait_pending(self):
        if not self._pending:
            return
        deadline = time.monotonic() + self.pending_wait
        while not os.path.exists(self._pending):
            if time.monotonic() > deadline:
                raise AEError(TIMEOUT)
            time.sleep(0.1)
        os.remove(self._pending)
        self._pending = None

    def run(self, template: str, args: dict, undo: str | None = None, helpers: str = ""):
        with self._lock:
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
            with open(path, encoding="utf-8") as f:
                res = json.load(f)
            os.remove(path)
            if not res.get("ok"):
                raise AEError("After Effects: " + res["error"]["message"])
            return res.get("data")
