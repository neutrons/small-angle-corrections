"""Command-line interface: usans-correct"""

import numpy as np
import click

from . import __version__, correct
from .config import load_config, require_transmission
from .io import load_profile, save_csv
from .diagnostics import assess
from .report import write_all
from pathlib import Path


@click.group()
@click.version_option(version=__version__, prog_name="usans-correct")
def main():
    """USANS post-processing correction framework.

    Use one of the subcommands below. Run 'usans-correct COMMAND --help'
    for details on each subcommand.
    """


# ---------------------------------------------------------------------------
# correct-ms subcommand
# ---------------------------------------------------------------------------

@main.command("correct-ms")
@click.option("--input",  "input_file",  required=True,
              type=click.Path(exists=True),
              help="Input CSV file with Q, I (and optionally dI) columns.")
@click.option("--config", "config_file", required=True,
              type=click.Path(exists=True),
              help="JSON5 configuration file.")
@click.option("--output", "output_dir",  required=True,
              help="Output directory (created if absent).")
@click.option("--transmission", "cli_transmission", default=None, type=float,
              help="Override transmission from config (0 < T < 1).")
@click.option("--verbose", is_flag=True, default=False,
              help="Print parameters and fit statistics.")
def correct_ms(input_file, config_file, output_dir,
               cli_transmission, verbose):
    """Apply multiple-scattering correction.

    Reads Q and I from INPUT_FILE (CSV with header row). All correction
    parameters come from CONFIG; --transmission overrides the config value.
    Writes 8 result files to OUTPUT_DIR.
    """
    overrides = {"transmission": cli_transmission} if cli_transmission is not None else {}
    cfg = load_config(config_file, overrides)
    transmission = require_transmission(cfg)

    n_basis      = int(cfg["n_basis"])
    n_orders     = int(cfg["n_orders"])
    length_scale = cfg.get("length_scale")
    if length_scale is not None:
        length_scale = float(length_scale)
    n_phi        = int(cfg["n_phi"])
    enforce_nonneg = bool(cfg["enforce_nonneg"])
    q_col        = cfg["q_col"]
    i_col        = cfg["i_col"]
    di_col       = cfg["di_col"]

    params_used = {
        "transmission":  transmission,
        "n_basis":       n_basis,
        "n_orders":      n_orders,
        "length_scale":  length_scale,
        "n_phi":         n_phi,
        "enforce_nonneg": enforce_nonneg,
    }

    if verbose:
        for k, v in params_used.items():
            click.echo(f"  {k:<18} = {v}")

    profile = load_profile(input_file, q_col=q_col, i_col=i_col, di_col=di_col)
    if verbose:
        click.echo(f"Read {profile.n_points} points from {input_file}")

    result = correct(
        profile.q, profile.I, transmission,
        n_basis=n_basis, n_orders=n_orders,
        length_scale=length_scale,
        enforce_nonneg=enforce_nonneg,
        n_phi=n_phi,
    )

    I_corr  = result["I_true"]
    I_fit   = result["I_fit"]
    alpha1  = result["alpha1"]
    I0      = float(result["I0"])
    opt     = result["result"]

    if profile.dI is not None:
        ratio   = np.where(np.abs(profile.I) > 1e-30,
                           np.abs(I_corr / profile.I), 1.0)
        dI_corr = profile.dI * ratio
    else:
        dI_corr = None

    if verbose:
        fit_rms = float(
            np.sqrt(np.mean((I_fit - profile.I) ** 2))
            / (np.mean(np.abs(profile.I)) + 1e-30)
        )
        click.echo(f"I0               = {I0:.4g}")
        click.echo(f"Fit RMS relative = {fit_rms:.3%}")
        click.echo(f"Optimizer        : {opt.message}")

    params_used["I0"] = I0

    write_all(
        out_dir     = Path(output_dir),
        profile_in  = profile,
        I_corr      = I_corr,
        I_fit       = I_fit,
        alpha1      = alpha1,
        dI_corr     = dI_corr,
        params_used = params_used,
        opt_result  = opt,
        input_file  = input_file,
        config_file = config_file,
        version     = __version__,
        cfg_raw     = cfg,
    )

    click.echo(f"Results written to: {output_dir}/")
    for f in sorted(Path(output_dir).iterdir()):
        click.echo(f"  {f.name}")


# ---------------------------------------------------------------------------
# diagnose subcommand
# ---------------------------------------------------------------------------

@main.command("diagnose")
@click.option("--input", "input_file", required=True,
              type=click.Path(exists=True),
              help="Input CSV file with Q and I columns.")
@click.option("--transmission", required=True, type=float,
              help="Sample transmission (0 < T < 1).")
@click.option("--verbose", is_flag=True, default=False,
              help="Print additional detail.")
def diagnose(input_file, transmission, verbose):
    """Report whether multiple-scattering correction is needed.

    Reads the input file and prints a plain-English assessment based on
    the transmission value. Does not apply any correction.
    """
    profile = load_profile(input_file)
    diag    = assess(profile, transmission)

    click.echo("")
    click.echo("USANS Diagnostics")
    click.echo("=" * 40)
    click.echo(f"  Input file   : {input_file}")
    click.echo(f"  Data points  : {diag['n_points']}")
    click.echo(f"  Q range      : {diag['q_min']:.4g} to {diag['q_max']:.4g}")
    click.echo(f"  I range      : {diag['I_min']:.4g} to {diag['I_max']:.4g}")
    click.echo("")
    click.echo(f"  Transmission : {diag['transmission']:.4f}")
    click.echo(f"  mu = -ln(T)  : {diag['mu']:.4f}")
    click.echo(f"  P1 (1-scat)  : {diag['P1']:.4f}")
    click.echo("")
    click.echo(f"  Assessment   : {diag['advice']}")
    click.echo("")


# ---------------------------------------------------------------------------
# desmear subcommand (placeholder)
# ---------------------------------------------------------------------------

@main.command("desmear")
@click.option("--input",  "input_file",  required=True,
              type=click.Path(exists=True))
@click.option("--config", "config_file", required=True,
              type=click.Path(exists=True))
@click.option("--output", "output_dir",  required=True)
def desmear(input_file, config_file, output_dir):
    """Slit desmearing correction (not yet implemented).

    This subcommand is reserved for a future Bonse-Hart slit desmearing
    correction. It will be available in a future version of usans-correct.
    """
    click.echo("")
    click.echo("Desmearing is not yet implemented.")
    click.echo("This feature is planned for a future version of usans-correct.")
    click.echo("See https://github.com/YOUR_ORG/usans-correct for updates.")
    click.echo("")
