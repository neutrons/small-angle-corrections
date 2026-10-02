"""JSON5 config loading and validation."""

import json
import re
from pathlib import Path

_DEFAULTS = {
    "n_basis": 12,
    "n_orders": 10,
    "length_scale": None,
    "n_phi": 32,
    "enforce_nonneg": False,
    "q_col": "Q",
    "i_col": "I",
    "di_col": "dI",
}


def load_json5(path) -> dict:
    """Load a JSON5 file (strips // line comments and /* */ block comments)."""
    text = Path(path).read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def load_config(path, cli_overrides: dict | None = None) -> dict:
    """
    Load config from a JSON5 file and apply CLI overrides.

    Accepts both 'basis_size' and 'n_basis' as keys (basis_size takes priority).
    Returns a merged dict with all DEFAULTS filled in.
    """
    file_cfg = load_json5(path)
    cfg = {**_DEFAULTS, **file_cfg}

    # Accept 'basis_size' as the user-facing alias for 'n_basis'
    if "basis_size" in cfg:
        cfg["n_basis"] = int(cfg["basis_size"])
    # Accept 'max_order' as alias for 'n_orders'
    if "max_order" in cfg:
        cfg["n_orders"] = int(cfg["max_order"])

    if cli_overrides:
        for k, v in cli_overrides.items():
            if v is not None:
                cfg[k] = v

    return cfg


def require_transmission(cfg: dict) -> float:
    """Extract transmission, raising UsageError if missing."""
    import click
    t = cfg.get("transmission")
    if t is None:
        raise click.UsageError(
            "transmission is required — set it in the config or via --transmission."
        )
    return float(t)
