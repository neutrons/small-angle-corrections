import json
from pathlib import Path

import numpy as np
from click.testing import CliRunner

from usans_correct.cli import main


def _make_csv(runner_dir, q_grid, profile):
    """Write a minimal input CSV and return its path string."""
    path = Path(runner_dir) / "input.csv"
    np.savetxt(path, np.column_stack([q_grid, profile]),
               delimiter=",", header="Q,I", comments="")
    return str(path)


def _make_config(runner_dir, transmission=0.7, n_basis=4, n_orders=4):
    """Write a minimal JSON5 config and return its path string."""
    cfg = {
        "transmission": transmission,
        "n_basis": n_basis,
        "n_orders": n_orders,
        "n_phi": 16,
        "enforce_nonneg": False,
    }
    path = Path(runner_dir) / "config.json5"
    path.write_text(json.dumps(cfg))
    return str(path)


def test_correct_ms_runs(q_grid, simple_profile, tmp_path):
    runner = CliRunner()
    csv_path = _make_csv(tmp_path, q_grid, simple_profile)
    cfg_path = _make_config(tmp_path)
    out_dir  = str(tmp_path / "out")

    result = runner.invoke(main, [
        "correct-ms",
        "--input",  csv_path,
        "--config", cfg_path,
        "--output", out_dir,
    ])
    assert result.exit_code == 0, result.output
    assert Path(out_dir, "corrected_profile.csv").exists()
    data = np.loadtxt(Path(out_dir, "corrected_profile.csv"),
                      delimiter=",", skiprows=1)
    assert data.shape[1] == 2   # Q, I_corrected (no dI in input)


def test_correct_ms_missing_config(q_grid, simple_profile, tmp_path):
    runner = CliRunner()
    csv_path = _make_csv(tmp_path, q_grid, simple_profile)
    result = runner.invoke(main, [
        "correct-ms",
        "--input",  csv_path,
        # --config intentionally omitted
        "--output", str(tmp_path / "out"),
    ])
    assert result.exit_code != 0


def test_diagnose_runs(q_grid, simple_profile, tmp_path):
    runner = CliRunner()
    csv_path = _make_csv(tmp_path, q_grid, simple_profile)
    result = runner.invoke(main, [
        "diagnose",
        "--input",        csv_path,
        "--transmission", "0.7",
    ])
    assert result.exit_code == 0, result.output
    assert "Assessment" in result.output


def test_desmear_not_implemented(q_grid, simple_profile, tmp_path):
    runner = CliRunner()
    csv_path = _make_csv(tmp_path, q_grid, simple_profile)
    cfg_path = _make_config(tmp_path)
    result = runner.invoke(main, [
        "desmear",
        "--input",  csv_path,
        "--config", cfg_path,
        "--output", str(tmp_path / "out"),
    ])
    assert result.exit_code == 0
    assert "not yet implemented" in result.output


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
