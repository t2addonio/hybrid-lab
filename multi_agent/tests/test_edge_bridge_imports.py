"""edge_bridge specialists must import regardless of the working directory."""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MODS = ["critic", "researcher", "coder", "architect"]


@pytest.mark.parametrize("cwd", [REPO, REPO / "edge_bridge", REPO / "multi_agent"])
def test_package_import(cwd):
    code = "import importlib\n" + "".join(
        f"importlib.import_module('edge_bridge.specialists.{m}')\n" for m in MODS)
    r = subprocess.run([sys.executable, "-c", code], cwd=cwd, capture_output=True, text=True,
                       env={"PYTHONPATH": str(REPO)})
    assert r.returncode == 0, r.stderr


def test_legacy_import_from_edge_bridge_dir():
    code = "import specialists.critic, specialists.coder, specialists.architect, specialists.researcher"
    r = subprocess.run([sys.executable, "-c", code], cwd=REPO / "edge_bridge", capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
