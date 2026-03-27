#!/usr/bin/env python3
"""integration/config_loader.py

Runtime config loader for strategy-owned YAML in strategy/config/**.

Design goals:
- No CANON changes.
- No extra deps beyond PyYAML (already in requirements.txt).
- Deterministic config hash (sha256 of file bytes) to log into forensics_events.

This is intentionally "thin": it validates only a minimal contract so the runner can start.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class LoadedConfig:
    path: str
    config: Dict[str, Any]
    config_hash: str  # sha256 hex
    strategy_name: str
    version: str


def _sha256_file(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha256(b).hexdigest()


def _require(d: Dict[str, Any], key: str) -> Any:
    if key not in d:
        raise ConfigError(f"Missing required key: {key}")
    return d[key]


def load_params_base(path: str = "strategy/config/params_base.yaml") -> LoadedConfig:
    """Load and minimally validate the strategy runtime config."""
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"Config not found: {p}")

    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError("params_base.yaml must be a YAML mapping (dict at top-level)")

    version = str(_require(raw, "version"))
    strategy_name = str(_require(raw, "strategy_name"))

    run = _require(raw, "run")
    if not isinstance(run, dict):
        raise ConfigError("run must be a mapping")

    mode = run.get("mode", "paper")
    if mode not in ("paper", "sim", "live"):
        raise ConfigError(f"run.mode must be one of paper|sim|live, got: {mode}")

    # Minimal subtrees expected by the iteration docs.
    for subtree in ("wallet_profile", "token_profile", "signals", "risk", "execution"):
        if subtree not in raw:
            raise ConfigError(f"Missing required subtree: {subtree}")

    return LoadedConfig(
        path=str(p),
        config=raw,
        config_hash=_sha256_file(p),
        strategy_name=strategy_name,
        version=version,
    )
