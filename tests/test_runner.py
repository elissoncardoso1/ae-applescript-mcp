"""Runner com osascript simulado: montagem da chamada e tradução de erros."""
import json
import re

import pytest

from ae_mcp.runner import AEError, AERunner

APP = '/Applications/Adobe After Effects 2027/Adobe "X".app'


class FakeOsa:
    """Imita o osascript; opcionalmente grava o arquivo de resultado como o AE faria."""

    def __init__(self, rc=0, stdout="0", stderr="", result=None):
        self.rc, self.stdout, self.stderr, self.result = rc, stdout, stderr, result
        self.calls = []

    def __call__(self, argv, stdin, timeout):
        self.calls.append((argv, stdin, timeout))
        if self.result is not None:
            path = re.search(r'new File\("([^"]+)"\)', argv[2]).group(1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(self.result))
        return self.rc, self.stdout, self.stderr


def make(fake, **kw):
    return AERunner(app_path=APP, timeout=5, override=True, exec_fn=fake, **kw)


def test_success_returns_data_and_passes_script_as_argv():
    fake = FakeOsa(result={"ok": True, "data": {"v": "27.0"}})
    assert make(fake).run("return 1;", {"s": "Olá — \"x\""}) == {"v": "27.0"}
    argv, applescript, _ = fake.calls[0]
    assert argv[:2] == ["osascript", "-"]
    assert "Olá" not in applescript and "DoScript (item 1 of argv)" in applescript
    assert 'Adobe \\"X\\".app' in applescript  # caminho escapado
    assert argv[3:] == ["1", "5"]  # override, timeout


def test_not_running():
    with pytest.raises(AEError, match="Abra o After Effects"):
        make(FakeOsa(stdout="AE_NOT_RUNNING")).run("return 1;", {})


def test_automation_denied():
    fake = FakeOsa(rc=1, stdout="", stderr="execution error: Not authorized to send Apple events (-1743)")
    with pytest.raises(AEError, match="Automação"):
        make(fake).run("return 1;", {})


def test_refused_without_result_file():
    with pytest.raises(AEError, match="recusou"):
        make(FakeOsa(stdout="1")).run("return 1;", {})


def test_extendscript_error_has_hint():
    fake = FakeOsa(result={"ok": False, "error": {"message": "Comp 'X' não encontrada"}})
    with pytest.raises(AEError, match="Comp 'X' não encontrada"):
        make(fake).run("return 1;", {})


def test_timeout_blocks_next_call_until_pending_finishes():
    fake = FakeOsa(rc=1, stdout="", stderr="AppleEvent timed out. (-1712)")
    r = make(fake, pending_wait=0.2)
    with pytest.raises(AEError, match="ainda está processando"):
        r.run("return 1;", {})
    with pytest.raises(AEError, match="ainda está processando"):
        r.run("return 1;", {})
    assert len(fake.calls) == 1  # a segunda chamada não foi enviada ao AE


def test_pending_cleared_when_late_result_arrives():
    fake = FakeOsa(rc=1, stdout="", stderr="(-1712)")
    r = make(fake, pending_wait=0.2)
    with pytest.raises(AEError):
        r.run("return 1;", {})
    open(r._pending, "w").write('{"ok": true, "data": null}')
    fake.rc, fake.stderr, fake.result = 0, "", {"ok": True, "data": 7}
    assert r.run("return 7;", {}) == 7
