import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]
def test_python_sources_compile():
    for path in (ROOT / "app").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
def test_cli_has_required_options():
    source=(ROOT/"tools/generate_audio.py").read_text(encoding="utf-8")
    for option in ("--mode", "--prompt", "--duration", "--name", "--seed", "--output", "--json"):
        assert option in source
def test_localhost_defaults_and_backcompat():
    assert '"127.0.0.1"' in (ROOT/"app/config.py").read_text(encoding="utf-8")
    api=(ROOT/"app/routers/api.py").read_text(encoding="utf-8")
    assert 'mode: str = "sfx"' in api and 'mode must be' in api
