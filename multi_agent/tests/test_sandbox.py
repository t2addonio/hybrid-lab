import json
import os
from pathlib import Path

import pytest

import core.sandbox as sb
from core import gate
from core.sandbox import Sandbox, SandboxError

BASE = Path(__file__).resolve().parent.parent


@pytest.fixture
def sandbox(monkeypatch):
    s = Sandbox()
    monkeypatch.setattr(sb, "_SANDBOX", s)
    return s


@pytest.fixture
def scratch():
    d = BASE / "workspace" / "_pytest_scratch"
    d.mkdir(parents=True, exist_ok=True)
    yield d
    for p in sorted(d.rglob("*"), reverse=True):
        p.unlink() if (p.is_file() or p.is_symlink()) else p.rmdir()
    d.rmdir()


@pytest.mark.parametrize("target", ["core/gate.py", "core/sandbox.py", "core/new.py",
                                    "config.yaml", "approve.py", "main.py", "state.json"])
def test_protected_and_unlisted_files_blocked(sandbox, target):
    for p in (target, BASE / target):
        with pytest.raises(SandboxError):
            sandbox.check_write(p, "x")


def test_write_file_handler_cannot_touch_gate(sandbox):
    before = (BASE / "core/gate.py").read_bytes()
    with pytest.raises(SandboxError):
        gate._write_file({"path": str(BASE / "core/gate.py"), "content": "pwned"})
    assert (BASE / "core/gate.py").read_bytes() == before


@pytest.mark.parametrize("target", ["workspace/../core/gate.py", "workspace/../../README.md",
                                    "proposals/../config.yaml", "../knowledge/x.md"])
def test_path_traversal_blocked(sandbox, target):
    with pytest.raises(SandboxError):
        sandbox.check_write(target, "x")


def test_tmp_blocked(sandbox):
    with pytest.raises(SandboxError):
        sandbox.check_write("/tmp/evil.txt", "x")
    assert sandbox.is_allowed("/tmp/x")  # reads of /tmp unchanged


def test_absolute_outside_blocked(sandbox):
    with pytest.raises(SandboxError):
        sandbox.check_write("/etc/passwd", "x")


def test_symlink_file_escape_blocked(sandbox, scratch):
    link = scratch / "link.py"
    link.symlink_to(BASE / "core" / "gate.py")
    with pytest.raises(SandboxError):
        sandbox.check_write(link, "x")


def test_symlink_dir_escape_blocked(sandbox, scratch, tmp_path):
    (scratch / "d").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(SandboxError):
        sandbox.check_write(scratch / "d" / "f.txt", "x")
    (scratch / "c").symlink_to(BASE / "core", target_is_directory=True)
    with pytest.raises(SandboxError):
        sandbox.check_write(scratch / "c" / "gate.py", "x")


def test_symlink_within_root_blocked(sandbox, scratch):
    (scratch / "real.txt").write_text("a")
    (scratch / "alias.txt").symlink_to(scratch / "real.txt")
    with pytest.raises(SandboxError):
        sandbox.check_write(scratch / "alias.txt", "x")


def test_allowed_writes(sandbox, scratch):
    rel = "workspace/_pytest_scratch/sub/note.md"
    res = gate._write_file({"path": rel, "content": "hello"})
    assert Path(res["path"]) == (BASE / rel).resolve()
    assert (BASE / rel).read_text() == "hello"
    assert sandbox.check_write(BASE / "proposals" / "X.md", "x") == BASE / "proposals" / "X.md"


def test_relative_path_anchored_at_base(sandbox, scratch, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert sandbox.check_write("workspace/_pytest_scratch/a.txt", "x") == \
        BASE / "workspace" / "_pytest_scratch" / "a.txt"


def test_root_dir_itself_not_a_file_target(sandbox):
    with pytest.raises(SandboxError):
        sandbox.check_write(BASE / "workspace", "x")


def test_max_write_bytes(sandbox, scratch):
    sandbox.max_write_bytes = 10
    with pytest.raises(SandboxError):
        sandbox.check_write(scratch / "big.txt", "x" * 11)


def test_write_roots_exist():
    Sandbox()
    assert (BASE / "workspace").is_dir() and (BASE / "proposals").is_dir()


@pytest.mark.parametrize("bad", ["a/b", "../evil", "..", "x.md", "a b", "a" * 129,
                                 "/etc/x", "a\\b", "id\n", 123])
def test_bad_patch_ids_rejected(sandbox, bad):
    with pytest.raises(ValueError):
        gate._propose_patch({"id": bad, "content": "CHANGE_PROPOSAL:\nx"})


def test_good_patch_id(sandbox, monkeypatch, tmp_path):
    log = BASE / "improvement_log.jsonl"
    before = log.read_bytes() if log.exists() else None
    pid = "PYTEST-ok_1"
    try:
        res = gate._propose_patch({"id": pid, "content": "body"})
        p = BASE / "proposals" / f"{pid}.md"
        assert Path(res["path"]) == p and p.read_text().startswith("CHANGE_PROPOSAL:")
        assert json.loads(log.read_text().splitlines()[-1])["id"] == pid
    finally:
        (BASE / "proposals" / f"{pid}.md").unlink(missing_ok=True)
        if before is None:
            log.unlink(missing_ok=True)
        else:
            log.write_bytes(before)


def test_default_patch_id_valid(sandbox):
    log = BASE / "improvement_log.jsonl"
    before = log.read_bytes()
    try:
        res = gate._propose_patch({"content": "body"})
        assert gate.PROPOSAL_ID_RE.fullmatch(res["proposal_id"])
    finally:
        Path(res["path"]).unlink(missing_ok=True)
        log.write_bytes(before)
