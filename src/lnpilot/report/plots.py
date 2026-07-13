"""Optional plots (requires matplotlib)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def plot_calibration(calibration: dict[str, Any], path: str | Path) -> Path:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError("pip install lnpilot[plot]") from exc

    xs = calibration.get("x_standards") or []
    ys = calibration.get("y_standards") or []
    slope = float(calibration["slope"])
    intercept = float(calibration["intercept"])

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(xs, ys, label="standards")
    if xs:
        xline = [min(xs), max(xs)]
        yline = [slope * x + intercept for x in xline]
        ax.plot(xline, yline, label=f"fit R²={calibration.get('r_squared', 0):.4f}")
    ax.set_xlabel("Concentration")
    ax.set_ylabel("Blank-corrected signal")
    ax.legend()
    ax.set_title("RiboGreen calibration")
    fig.tight_layout()
    fig.savefig(p, dpi=120)
    plt.close(fig)
    return p
