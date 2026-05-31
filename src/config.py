"""Carregamento de configuração e segredos (.env / config.yaml)."""
from __future__ import annotations
import os, yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _expand(obj):
    if isinstance(obj, dict):
        return {k: _expand(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand(v) for v in obj]
    if isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        return os.getenv(obj[2:-1], "")
    return obj

def load_config(path: str | None = None) -> dict:
    cfg_path = Path(path) if path else (ROOT / "config" / "config.yaml")
    if not cfg_path.exists():
        cfg_path = ROOT / "config" / "config.example.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return _expand(yaml.safe_load(f))
