"""Sleep configuration stays readable independently of the process locale."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from skillopt_sleep import config


@pytest.mark.parametrize("suffix", ["json", "yaml", "yml"])
def test_utf8_config_survives_a_non_utf8_locale(tmp_path: Path, suffix: str) -> None:
    values = {
        "backend": "codex",
        "preferences": "Use résumé examples and 中文说明.",
        "target_skill_path": "技能/SKILL.md",
    }
    path = tmp_path / f"config.{suffix}"
    if suffix == "json":
        text = json.dumps(values, ensure_ascii=False)
    else:
        yaml = pytest.importorskip("yaml")
        text = yaml.safe_dump(values, allow_unicode=True)
    path.write_text(text, encoding="utf-8")

    script = """
import json
import sys
from skillopt_sleep import config

config.HOME_STATE_DIR = sys.argv[1]
expected = json.loads(sys.argv[2])
loaded = config.load_config()
for key, value in expected.items():
    assert loaded.get(key) == value, (key, loaded.get(key), value)
assert set(expected) <= set(loaded.get("_user_config_keys"))
overridden = config.load_config(backend="claude", preferences=None)
assert overridden.backend == "claude"
assert overridden.preferences == expected["preferences"]
"""
    env = {
        **os.environ,
        "LC_ALL": "C",
        "PYTHONUTF8": "0",
        "PYTHONCOERCECLOCALE": "0",
    }
    root = str(Path(config.__file__).resolve().parent.parent)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [root, env.get("PYTHONPATH")]))
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path), json.dumps(values)],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
