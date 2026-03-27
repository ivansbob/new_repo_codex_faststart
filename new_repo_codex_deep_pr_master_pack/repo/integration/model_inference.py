"""Model inference interface.

This repo is model-off first: the pipeline must run deterministically even when
no model artifact is available.

This module exists to pin the extension point for miniML / later model work.
"""

from __future__ import annotations

from typing import Dict, Optional


def infer_p_model(features: Dict[str, float], *, mode: str = "model_off") -> Optional[float]:
    """Return model probability/confidence for the trade.

    Current behavior:
    - mode == "model_off": returns None.

    Future: load a model artifact and return a float in [0, 1].
    """

    if mode != "model_off":
        # Stub: unknown modes are treated as model_off for now.
        return None
    return None
