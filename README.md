# small-angle-corrections

**Post-processing corrections for small-angle scattering data (neutron and X-ray) — step-by-step guide**

---

## 1. What This Package Does

`small-angle-corrections` is a toolkit of post-processing corrections for reduced small-angle scattering data — SANS, SAXS, and USANS, from neutron or X-ray instruments. The first supported correction is **multiple-scattering correction**, with ultra-small-angle neutron scattering (USANS) as the first use case. Slit desmearing (for Bonse-Hart USANS instruments) is planned as a future subcommand.

### Multiple-scattering correction

When you measure a sample on a USANS instrument, most neutrons pass straight through and a small fraction scatter once off the structures inside your sample. That single-scattering signal is what you actually want — it tells you the real size and shape of whatever you are studying. The problem is that some neutrons scatter *more than once* before they leave the sample. These multiply-scattered neutrons end up mixed in with the singly-scattered ones, and the mixture looks like a smeared, artificially broadened version of the true signal. The thicker or denser your sample, the worse this effect gets.

This software unmixes the multiply-scattered contribution and gives you back the true single-scattering profile. It does this by building a mathematical model of how multiple scattering smears your data (using a technique called algebraic convolution, described by Tung et al.), then running an optimisation that finds the unsmeared profile that, when re-smeared, best reproduces what you actually measured. You tell it how strongly your sample scatters by providing the *transmission* — the fraction of neutrons that pass through without interacting — and the algorithm takes care of the rest.

At the end you get a corrected data file (your main result), a plot showing the before and after, and a set of diagnostic files that tell you how well the correction worked. The corrected profile can be used directly in any downstream analysis software just like any other reduced dataset.

---

## 2. Requirements

| Requirement | Notes |
|---|---|
| Operating system | macOS, Linux, or Windows |
| Python | Version 3.11 (see below) |
| miniforge / mamba | Recommended way to manage Python (see below) |
| numpy, scipy, click, matplotlib | Installed automatically |

**What is Python?** Python is the programming language this software is written in. You do not need to write any Python yourself to use the command-line tool, but you do need a working Python installation.

**Why miniforge / mamba?** Scientific software often requires very specific versions of its dependencies, and those requirements can clash across different projects. `miniforge` gives you isolated *environments* — self-contained boxes where you can install exactly the right versions without breaking anything else on your computer. `mamba` is a faster version of the `conda` package manager that comes with miniforge.

**Install miniforge** (do this once, skip if you already have it):
Go to [https://github.com/conda-forge/miniforge](https://github.com/conda-forge/miniforge) and follow the instructions for your operating system. After installation, close and reopen your terminal.

**Dependencies installed automatically** when you run the install command below:
- `numpy` — fast numerical arrays
- `scipy` — scientific computing (optimisation, integration)
- `click` — command-line interface
- `matplotlib` — plots
- `pytest` — testing (dev only)

---

## 3. Installation

Follow these steps exactly, one at a time. Each step builds on the previous one.

### Step 1 — Download the repository

Open a terminal and run:

```bash
git clone https://github.com/yrshang/small-angle-corrections.git
cd small-angle-corrections
```

You should now be inside the `small-angle-corrections` folder. You can check by running `ls` (macOS/Linux) or `dir` (Windows) — you should see files like `pyproject.toml`, `README.md`, and a folder called `src`.

> **No git?** You can also download a ZIP from the repository page (green "Code" button → "Download ZIP"), unzip it, and `cd` into the resulting folder.

### Step 2 — Create a dedicated conda environment

This creates an isolated box called `sac` with Python 3.11 inside it:

```bash
mamba create -n sac python=3.11 -y
```

Expected output (last few lines):
```
Preparing transaction: done
Verifying transaction: done
Executing transaction: done
#
# To activate this environment, use
#
#     $ conda activate sac
```

### Step 3 — Activate the environment

```bash
conda activate sac
```

Your terminal prompt should now start with `(sac)` to show the environment is active. **You need to do this every time you open a new terminal.**

### Step 4 — Install the package

```bash
pip install -e ".[dev]"
```

The `-e` flag means "editable install" — changes to the source files take effect immediately without reinstalling. `[dev]` also installs the testing tools.

Expected output (last few lines):
```
Successfully installed click-8.x numpy-2.x scipy-1.x small-angle-corrections-0.1.0
```

### Step 5 — Verify the installation

```bash
small-angle-corrections --help
```

Expected output:
```
Usage: small-angle-corrections [OPTIONS] COMMAND [ARGS]...

  Small-angle scattering (SANS/SAXS/USANS) post-processing correction
  framework.

  Use one of the subcommands below. Run 'small-angle-corrections COMMAND
  --help' for details on each subcommand.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  correct-ms  Apply multiple-scattering correction.
  desmear     Slit desmearing correction (not yet implemented).
  diagnose    Report whether multiple-scattering correction is needed.
```

The tool is organised into subcommands:

| Subcommand | What it does |
|---|---|
| `correct-ms` | Apply the multiple-scattering correction (Section 5) |
| `diagnose` | Print a quick assessment of whether correction is needed, without correcting (Section 10) |
| `desmear` | Reserved for slit desmearing — not yet implemented |

Run `small-angle-corrections COMMAND --help` to see the options for any subcommand.

If you see this, the installation worked. If you see `command not found`, go to the Troubleshooting section.

---

## 4. Preparing Your Input Data

### What is a CSV file?

CSV stands for "comma-separated values." It is a plain text file where each row is one data point and each column is separated by a comma. You can create one from Excel (File → Save As → CSV), from Igor Pro, or from your instrument's reduction software.

### Required column format

Your input file must have a header row with these exact column names (case-insensitive):

```
Q,I,dI
```

- **Q** — momentum transfer in Å⁻¹ (or whatever units your instrument uses — just be consistent)
- **I** — measured apparent intensity at that Q value
- **dI** — uncertainty (error bar) on I; usually the standard deviation from counting statistics

A real file looks like this:

```
Q,I,dI
0.00010,125.4,3.2
0.00013,124.9,3.1
0.00017,123.8,3.0
0.00022,121.5,2.9
0.00029,117.2,2.8
```

### Where does the transmission value come from?

The transmission T is measured on your beamline as part of the standard data reduction procedure. It is the ratio of the count rate through your sample to the count rate through an empty cell (or air). It is a number between 0 and 1:
- T = 1.0 means no scattering or absorption at all (not physical, but the theoretical limit)
- T = 0.9 means 10 % of neutrons were scattered or absorbed
- T = 0.5 means half the neutrons were scattered or absorbed

Your instrument scientist or reduction software will give you this number. Write it down — you will need it for the config file.

### What if I don't have dI?

The `dI` column is optional. If your file only has `Q` and `I`, that is fine:

```
Q,I
0.00010,125.4
0.00013,124.9
```

The correction will run without uncertainty information, but the output `corrected_profile.csv` will not have an uncertainty column. If you can get dI from your reduction software, it is always better to include it.

---

## 5. Running the Correction

### The basic command

```bash
small-angle-corrections correct-ms \
  --input  my_sample.csv \
  --config example_config.json5 \
  --output results/my_sample/
```

On Windows, replace the `\` line-continuation characters with `^`:

```
small-angle-corrections correct-ms ^
  --input  my_sample.csv ^
  --config example_config.json5 ^
  --output results/my_sample/
```

### What each `correct-ms` flag does

| Flag | What it does |
|---|---|
| `--input` | Path to your data file (the CSV described in Section 4) |
| `--config` | Path to your configuration file (described in Section 6) |
| `--output` | Folder where all results will be saved; created automatically if it does not exist |
| `--transmission` | *(optional)* Override the transmission value from the config file on the fly |
| `--verbose` | *(optional)* Print extra information while running so you can see what is happening |

To check your data without applying the correction, use the separate `diagnose` subcommand (see Section 10).

### A complete real example

```bash
small-angle-corrections correct-ms \
  --input  examples/data/synthetic_reduced_profile.csv \
  --config examples/example_config.json5 \
  --output results/my_first_run/ \
  --verbose
```

While it runs, you will see output like:

```
  transmission       = 0.5
  n_basis            = 12
  n_orders           = 10
  length_scale       = None
  n_phi              = 32
  enforce_nonneg     = False
Read 80 points from examples/data/synthetic_reduced_profile.csv
I0               = 0.514
Fit RMS relative = 1.876%
Optimizer        : `ftol` termination condition is satisfied.
Results written to: results/my_first_run/
  coefficients.csv
  config_used.json5
  corrected_profile.csv
  correction_report.json
  correction_report.txt
  correction_summary.png
  diagnostics.json
  fitted_apparent_profile.csv
  original_profile.csv
```

### What you get in the output folder

After the command finishes, the output folder will contain exactly these 9 files:

| File | Plain-English description |
|---|---|
| `corrected_profile.csv` | **Your main result.** The corrected intensity vs Q. Use this in your analysis. |
| `fitted_apparent_profile.csv` | How well the model reproduced your input data. |
| `original_profile.csv` | A copy of your input data, saved for reference. |
| `coefficients.csv` | The internal basis coefficients of the recovered profile. |
| `diagnostics.json` | Machine-readable fit statistics (useful for scripting). |
| `correction_report.json` | Machine-readable summary of everything that was done. |
| `correction_report.txt` | Human-readable version of the correction report. |
| `config_used.json5` | The exact settings that were used, saved for reproducibility. |
| `correction_summary.png` | Plot showing apparent input, model fit, and corrected output. |

---

## 6. Configuration File

### What is a config file and why does it exist?

Instead of typing all your settings on the command line every time, you keep them in a configuration file. This makes your analysis reproducible — you can share the config file with a colleague and they can run the exact same correction on the exact same data.

The config file uses **JSON5 format**, which is like a simple text file where settings are written as `"name": value`. The `//` prefix marks a comment — text that is ignored by the software but helps you remember what each setting does.

### The example config file explained

Open `examples/example_config.json5` — here is what every field means:

```json5
{
  // -----------------------------------------------------------------------
  // small-angle-corrections configuration (correct-ms subcommand)
  // -----------------------------------------------------------------------

  // *** CHANGE THIS to your measured sample transmission. ***
  // It is a number between 0 and 1.
  // Example: T=0.85 means 85% of neutrons passed through your sample.
  "transmission": 0.5,

  // Number of mathematical basis functions used to represent your scattering
  // profile. More basis functions = more detail captured, but also more
  // sensitive to noise. 8 is a safe default for most USANS data.
  "n_basis": 8,

  // How many scattering orders to include in the forward model.
  // 10 is more than enough for transmission > 0.1.
  // Leave this at the default unless you have very strong scatterers.
  "n_orders": 10,

  // Internal Q scaling factor. null means the software chooses automatically
  // (recommended). Only change this if you have a specific reason to.
  "length_scale": null,

  // Number of integration points used inside the mathematical calculation.
  // 32 is accurate for typical scattering profiles. Leave as default.
  "n_phi": 32,

  // Whether to force the recovered scattering profile to be non-negative.
  // false works for most samples. Set to true if you get unphysical
  // negative intensity values in the corrected output.
  "enforce_nonneg": false,

  // Names of the columns in your input CSV file (case-insensitive).
  // Change these only if your file uses different column headers.
  "q_col": "Q",
  "i_col": "I",
  "di_col": "dI"
}
```

### What do I need to change?

For a typical new experiment, **you only need to change one thing**:

```json5
"transmission": 0.5,   // ← replace 0.5 with your actual transmission value
```

Everything else can stay at the default. Once you are comfortable with the software, you can explore `n_basis` if you have noisy data or fine-featured profiles.

### Overriding transmission on the command line

If you are processing several samples with different transmissions, you can override the transmission without editing the config file:

```bash
small-angle-corrections correct-ms \
  --input  sample_A.csv \
  --config my_config.json5 \
  --output results/sample_A/ \
  --transmission 0.72
```

The `--transmission` flag always wins over the value in the config file.

---

## 7. Understanding the Output

### `corrected_profile.csv` — your main result

This is the file you will use in your analysis. It has the same Q column as your input, plus the corrected intensity and (if dI was provided) a propagated uncertainty:

```
Q,I_corrected,dI_corrected
0.00010,132.1,3.4
0.00013,131.5,3.3
...
```

Import this into Igor Pro, SasView, or any other analysis software exactly as you would import your original reduced data.

### `fitted_apparent_profile.csv` — model fit to your data

Contains the forward-model prediction of what your input data *should* look like given the recovered profile. If the correction worked well, these values will be very close to your original `I` column. A large mismatch means the model struggled to fit your data — check the diagnostics.

### `diagnostics.json` — fit statistics

A machine-readable file with numbers that tell you how the correction went:

- **`fit_rms_relative`** — the relative root-mean-square difference between the fitted apparent profile and your input data. Values below 5 % are good; values above 10 % suggest the fit struggled.
- **`optimizer_success`** — `true` if the fitting converged properly.
- **`optimizer_message`** — a short sentence saying why the optimiser stopped.
- **`I0`** — a scale factor the algorithm found. Values near 1.0 are healthy; values far from 1.0 (e.g., 0.001 or 1000) can indicate problems — see Troubleshooting.

### `correction_report.txt` — human-readable summary

Open this in any text editor for a plain-text summary of exactly what was done: input file, config values used, and fit statistics. Good for your lab notebook.

### `correction_summary.png` — the before-and-after plot

This is the most useful file for quickly judging whether the correction made sense.

**What to look for:**

- The **blue line** (Apparent input) is your raw measured data.
- The **green dashed line** (Fitted apparent) should lie almost exactly on top of the blue line. If it does not, the model did not fit your data well.
- The **red line** (Corrected) is your result. For a well-scattered sample it should be sharper (less spread out at large Q) and higher at small Q than the apparent profile.
- The **lower panel** shows residuals — how far the model fit is from your data, as a percentage. Residuals within ±5 % across the whole Q range indicate a good fit.

If the red line looks almost identical to the blue line, your sample may not need correction (low multiple scattering). If the red and blue lines are very different, your sample is a strong scatterer and the correction is important.

---

## 8. Running the Synthetic Demo

### What the demo does

The demo generates a completely fake dataset where we know the exact answer, applies the correction, and checks how well the software recovered the truth. It is a good way to verify that your installation is working correctly and to understand what the output should look like.

### Run it

```bash
python examples/synthetic_demo.py
```

This will take about 30–90 seconds depending on your computer.

### What you should see

```
Saved: examples/data/synthetic_reduced_profile.csv
Saved: examples/data/synthetic_demo.png
RMS relative error  apparent vs true : 53.8%
RMS relative error  recovered vs true: 15.6%
I0 recovered: 1.3899  (expected ~1.0)
```

**What do these numbers mean?**

- The **apparent profile** (what the instrument would measure) differs from the true profile by about 54 % — that is how much multiple scattering has distorted the data in this synthetic example.
- After correction, the **recovered profile** differs from the truth by only about 16 % — a factor of 3 improvement.
- **I0 recovered** should ideally be 1.0. Values between 0.5 and 2.0 are generally acceptable; it is a scale factor absorbed by the fitting.

Open `examples/data/synthetic_demo.png` to see the figure. You should see:
- A black line (True primary profile)
- A blue dashed line (Apparent, smeared by multiple scattering)
- A green dotted line (Fitted apparent — the model re-smearing the recovered profile; should match the blue line)
- A red line (Recovered primary — should be close to the black line)

If all four curves are present and the recovered (red) is visibly closer to the true (black) than the apparent (blue) is, the software is working correctly.

---

## 9. Python API

For users who want to call the correction from their own Python scripts rather than the command line.

```python
import numpy as np
from small_angle_corrections import correct

# Load your data (Q in Å⁻¹, I in any consistent units)
data = np.loadtxt('my_sample.csv', delimiter=',', skiprows=1)
q = data[:, 0]          # first column: Q
I_apparent = data[:, 1] # second column: I

# Run the correction
# transmission: your measured sample transmission (0 to 1)
result = correct(q, I_apparent, transmission=0.5)

# The corrected (true single-scattering) profile
I_corrected = result['I_true']    # shape (n_q,) — same length as q

# How well the model re-fits your input data
I_fit = result['I_fit']           # should be close to I_apparent

# Overall intensity scale factor found by the fitting
I0 = result['I0']                 # healthy range: 0.1 to 10

# Save the corrected profile
np.savetxt('corrected.csv',
           np.column_stack([q, I_corrected]),
           delimiter=',', header='Q,I_corrected', comments='')
```

For more control, use `AlgebraicConvolutionModel` directly:

```python
from small_angle_corrections import AlgebraicConvolutionModel

model = AlgebraicConvolutionModel(q, n_basis=10, n_orders=8)
result = model.invert(I_apparent, transmission=0.5, enforce_nonneg=False)
```

---

## 10. When to Apply This Correction

The need for correction depends on how much your sample scatters. The transmission value T is the easiest guide:

| Transmission T | Guidance |
|---|---|
| T > 0.9 | Multiple scattering is small. Correction is optional; check the plot first. |
| 0.7 ≤ T ≤ 0.9 | Noticeable multiple scattering. Correction is recommended. |
| 0.3 ≤ T < 0.7 | Significant multiple scattering. Correction is important. |
| T < 0.3 | Strong multiple scattering. Correction is essential, but interpret results carefully — the fitting problem becomes harder at very low transmission. |

**Not sure whether to correct?** Run the `diagnose` subcommand first:

```bash
small-angle-corrections diagnose \
  --input        my_sample.csv \
  --transmission 0.72
```

This reads your data, prints its Q and intensity range, the scattering power μ = −ln(T) and single-scattering probability, and a plain-English assessment of whether correction is needed. It does not apply any correction or write any files.

**A useful rule of thumb:** if the apparent and corrected profiles look nearly identical in the summary plot, the correction is probably not needed. If they look noticeably different, apply it.

---

## 11. Troubleshooting

### `command not found: small-angle-corrections`

You either did not run `pip install -e .` (go back to Installation Step 4), or your conda environment is not active.

```bash
conda activate sac
pip install -e .
small-angle-corrections --help
```

---

### `No module named small_angle_corrections`

You are in the wrong conda environment. Check which environments you have:

```bash
conda env list
```

Activate the correct one:

```bash
conda activate sac
```

---

### `transmission is required — set it in the config or via --transmission`

You did not set the transmission value. Open your config file and make sure this line is present and has a real number (not `null`):

```json5
"transmission": 0.72,
```

Or pass it on the command line:

```bash
small-angle-corrections correct-ms --input data.csv --config config.json5 --output out/ --transmission 0.72
```

---

### `Column 'Q' not found` (or `'I'`, or `'dI'`)

The column names in your CSV file do not match what the config file expects. Either:

1. Open your CSV file and check the header row. Make sure it has `Q`, `I`, and optionally `dI` (capitalisation does not matter).
2. Or update the config file to use your actual column names:
   ```json5
   "q_col": "q_ang_inv",
   "i_col": "intensity",
   ```

---

### `recovered I0 far from 1.0` (e.g., I0 = 0.00001 or I0 = 50000)

`I0` is a scale factor the fitting algorithm uses to match the overall intensity level between the model and your data. A value far from 1.0 usually means one of the following:

- Your data has very different units than expected — this is fine, the correction still works.
- The fitting converged to a wrong solution — try setting `enforce_nonneg: true` in the config, or reduce `n_basis` to 4 or 6.
- There is a problem with the input data (e.g., negative intensities, NaN values, zero transmission) — check your CSV file.

---

### The corrected profile looks worse than the input

This sometimes happens with profiles that have oscillatory features (form factor oscillations, interference peaks). Try:

1. Narrow the Q range to the smooth low-Q part of your data.
2. Increase `n_basis` to 10 or 12 in the config.
3. Set `enforce_nonneg: false` in the config (the default is already `false`).

---

### Running the tests to check the installation

If you suspect something is broken, run the test suite:

```bash
cd small-angle-corrections
pytest tests/ -v
```

Expected output (last line):
```
20 passed in 3.0s
```

If any tests fail, note the name of the failing test and the error message, and report it as a GitHub issue.

---

## 12. Citation

If you use this software in a publication, please cite both the software and the underlying method paper.

**Plain-text citation:**

> ORNL USANS Team. *small-angle-corrections* (version 0.1.0). 2026. https://github.com/yrshang/small-angle-corrections
> Based on: Tung et al., "Multiple scattering correction for USANS measurements,"
> *Journal of Applied Crystallography*.

**BibTeX entry for the software:**

```bibtex
@software{small_angle_corrections,
  author  = {{ORNL USANS Team}},
  title   = {small-angle-corrections: Post-processing corrections for small-angle scattering data},
  version = {0.1.0},
  year    = {2026},
  url     = {https://github.com/yrshang/small-angle-corrections},
  license = {MIT}
}
```

**BibTeX entry for the method paper:**

```bibtex
@article{tung_usans_ms,
  author  = {Tung, N.-H. and others},
  title   = {Multiple scattering correction for USANS measurements},
  journal = {Journal of Applied Crystallography},
  note    = {See CITATION.cff for full reference details}
}
```

The file `CITATION.cff` in the root of this repository contains machine-readable citation metadata that GitHub and Zenodo can read automatically.
