# LNPilot

**Reproducible mRNA–LNP development from sequence to vial**

LNPilot is an open-source Python toolkit for **verified** mRNA–lipid nanoparticle (LNP) batch planning and raw RiboGreen plate analysis. It produces unit-aware, machine-readable experimental records and transparent Markdown/CSV/JSON reports.

> **Not regulatory software.** v0.1 is *verified* against its equations and reference cases. It is **not** validated for GxP or regulatory use.

## Install

```bash
pip install -e ".[dev]"
```

Optional extras: `[plate]` (XLSX), `[plot]` (calibration plots), `[yaml]` (YAML batch configs).

Core dependencies: NumPy, Pint. No CUDA, Torch, or ViennaRNA.

## Quick start

```python
from lnpilot import plan_batch, analyze_ribogreen_plate

plan = plan_batch(
    rna_mass="100 ug",
    target_np=6,
    lipid_composition={
        "ionizable": {"mol_percent": 50.0, "mw": "710 g/mol", "stock": "10 mg/mL"},
        "helper": {"mol_percent": 10.0, "mw": "790 g/mol", "stock": "10 mg/mL"},
        "cholesterol": {"mol_percent": 38.5, "mw": "386.65 g/mol", "stock": "10 mg/mL"},
        "peg_lipid": {"mol_percent": 1.5, "mw": "2500 g/mol", "stock": "5 mg/mL"},
    },
    frr="3:1 aqueous:organic",
    total_flow_rate="12 mL/min",
    expected_recovery=0.80,
)

assay = analyze_ribogreen_plate(
    data="examples/plate_reader_example.csv",
    plate_map="examples/plate_map_example.csv",
)
```

## CLI

```bash
lnpilot plan-batch examples/batch_example.json --out results/
lnpilot analyze-ribogreen examples/plate_reader_example.csv --map examples/plate_map_example.csv --out results/
lnpilot render-report results/batch-plan.json
```

## v0.1 scope

| Workflow | Purpose |
|----------|---------|
| `plan_batch()` | N/P, lipid composition, stocks, FRR/TFR mixing, mass balance |
| `analyze_ribogreen_plate()` | Plate map + calibration → free/total RNA, EE%, recovery |

**Deferred:** IVT, construct/folding, DLS/pKa, stability, expression PK/PD, ML/GPU.

## Scientific notes

- FRR must be explicit (`3:1 aqueous:organic` or `organic:aqueous`); never inferred.
- RNA phosphate uses a **mass-based average nucleotide MW** approximation unless stated otherwise.
- Junction ethanol fraction is at the mixer, not after dilution/dialysis/TFF.
- RiboGreen reports dye-accessible RNA; high EE% ≠ potency.

See [docs/equations.md](docs/equations.md).

## Tests

```bash
pytest -q
ruff check src tests
```

CI runs on Python 3.10–3.12 (`.github/workflows/ci.yml`).

## Project layout

```text
src/lnpilot/   core, formulate, characterize, io, report, cli
examples/      sample batch config + RiboGreen plate
docs/          canonical equations
tests/         unit, property, CLI, and reference cases
```

## License

MIT
