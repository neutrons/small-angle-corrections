"""Write the suite of output files for a completed correction run."""

import json
import datetime
from pathlib import Path

import numpy as np

from .io import save_csv
from .profiles import Profile


def write_all(
    out_dir: Path,
    profile_in: Profile,
    I_corr: np.ndarray,
    I_fit: np.ndarray,
    alpha1: np.ndarray,
    dI_corr,
    params_used: dict,
    opt_result,
    input_file: str,
    config_file: str,
    version: str,
    cfg_raw: dict,
) -> None:
    """Write all 9 output files to out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

    q   = profile_in.q
    I   = profile_in.I
    dI  = profile_in.dI

    # 1. original_profile.csv
    if dI is not None:
        save_csv(out_dir / "original_profile.csv",
                 ["Q", "I", "dI"], [q, I, dI])
    else:
        save_csv(out_dir / "original_profile.csv", ["Q", "I"], [q, I])

    # 2. corrected_profile.csv
    if dI_corr is not None:
        save_csv(out_dir / "corrected_profile.csv",
                 ["Q", "I_corrected", "dI_corrected"], [q, I_corr, dI_corr])
    else:
        save_csv(out_dir / "corrected_profile.csv",
                 ["Q", "I_corrected"], [q, I_corr])

    # 3. fitted_apparent_profile.csv
    save_csv(out_dir / "fitted_apparent_profile.csv",
             ["Q", "I_fit"], [q, I_fit])

    # 4. coefficients.csv
    if len(alpha1):
        save_csv(out_dir / "coefficients.csv",
                 ["l", "alpha1"],
                 [np.arange(len(alpha1), dtype=float), alpha1])
    else:
        (out_dir / "coefficients.csv").write_text("l,alpha1\n")

    # 5. diagnostics.json
    I0 = float(params_used.get("I0", float("nan")))
    fit_rms = float(
        np.sqrt(np.mean((I_fit - I) ** 2)) / (np.mean(np.abs(I)) + 1e-30)
    )
    diag = {
        "n_points": profile_in.n_points,
        **{k: v for k, v in params_used.items() if k != "I0"},
        "I0":                 I0,
        "fit_rms_relative":   fit_rms,
        "optimizer_cost":     float(opt_result.cost),
        "optimizer_nfev":     int(opt_result.nfev),
        "optimizer_success":  bool(opt_result.success),
        "optimizer_message":  str(opt_result.message),
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2))

    # 6. correction_report.json
    report = {
        "version":    version,
        "timestamp":  timestamp,
        "input_file": str(Path(input_file).resolve()),
        "config_file": str(Path(config_file).resolve()),
        "output_dir": str(out_dir.resolve()),
        "parameters": params_used,
        "results": {
            "I0":               I0,
            "fit_rms_relative": fit_rms,
            "optimizer_cost":   float(opt_result.cost),
            "optimizer_success": bool(opt_result.success),
        },
    }
    (out_dir / "correction_report.json").write_text(json.dumps(report, indent=2))

    # 7. correction_report.txt
    _write_text_report(out_dir / "correction_report.txt", report, diag)

    # 8. config_used.json5
    _write_config_json5(out_dir / "config_used.json5", cfg_raw, params_used, timestamp)

    # 9. correction_summary.png
    _write_plot(out_dir / "correction_summary.png",
                q, I, I_fit, I_corr,
                dI=dI,
                transmission=params_used.get("transmission"))


def _write_text_report(path: Path, report: dict, diag: dict) -> None:
    lines = [
        "Small-Angle Scattering Multiple-Scattering Correction Report",
        "=" * 60,
        f"Version    : {report['version']}",
        f"Timestamp  : {report['timestamp']}",
        f"Input      : {report['input_file']}",
        f"Config     : {report['config_file']}",
        f"Output dir : {report['output_dir']}",
        "", "Parameters", "-" * 24,
    ]
    for k, v in report["parameters"].items():
        lines.append(f"  {k:<18}: {v}")
    lines += ["", "Results", "-" * 24]
    for k, v in report["results"].items():
        fmt = f"{v:.6g}" if isinstance(v, float) else str(v)
        lines.append(f"  {k:<26}: {fmt}")
    path.write_text("\n".join(lines) + "\n")


def _write_config_json5(path: Path, cfg: dict, params: dict, timestamp: str) -> None:
    merged = {**cfg, **params}
    items  = list(merged.items())
    lines  = ["{", f"  // Config actually used — generated {timestamp}"]
    for i, (k, v) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        if isinstance(v, str):
            lines.append(f'  "{k}": "{v}"{comma}')
        elif v is None:
            lines.append(f'  "{k}": null{comma}')
        elif isinstance(v, bool):
            lines.append(f'  "{k}": {"true" if v else "false"}{comma}')
        else:
            lines.append(f'  "{k}": {v}{comma}')
    lines.append("}")
    path.write_text("\n".join(lines) + "\n")


def _write_plot(path: Path, q, I_app, I_fit, I_corr,
                dI=None, transmission=None) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return

    fig, (ax, ax_res) = plt.subplots(
        2, 1, figsize=(7, 7),
        gridspec_kw={"height_ratios": [3, 1]},
    )
    if dI is not None:
        ax.fill_between(q, np.maximum(I_app - dI, 1e-30), I_app + dI,
                        alpha=0.2, color="steelblue")
    ax.semilogy(q, I_app,  "b-",  lw=1.5, label="Apparent (input)")
    ax.semilogy(q, I_fit,  "g--", lw=1.2, label="Fitted apparent")
    ax.semilogy(q, I_corr, "r-",  lw=2.0, label="Corrected")
    title = "Multiple-Scattering Correction"
    if transmission is not None:
        title += f"  (T = {transmission:.3f})"
    ax.set_title(title)
    ax.set_ylabel("Intensity (a.u.)")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)

    with np.errstate(divide="ignore", invalid="ignore"):
        rel_res = np.where(I_app > 0, (I_fit - I_app) / I_app * 100.0, 0.0)
    ax_res.axhline(0, color="k", lw=0.8, ls="--")
    ax_res.plot(q, rel_res, "g-", lw=1.2)
    ax_res.set_xlabel("Q (a.u.)")
    ax_res.set_ylabel("Fit residual (%)")
    ax_res.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
