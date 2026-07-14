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

    residuals = calibration.get("residuals") or []
    fig, (ax, residual_ax) = plt.subplots(
        2,
        1,
        figsize=(6, 6),
        gridspec_kw={"height_ratios": [2, 1]},
        sharex=True,
    )
    ax.scatter(xs, ys, label="standard-level means")
    if xs:
        xline = [min(xs), max(xs)]
        yline = [slope * x + intercept for x in xline]
        ax.plot(xline, yline, label=f"fit R²={calibration.get('r_squared', 0):.4f}")
    ax.set_ylabel("Blank-corrected signal")
    ax.legend()
    ax.set_title("RiboGreen calibration")
    residual_ax.axhline(0, color="black", linewidth=0.8)
    residual_ax.scatter(xs, residuals, color="tab:red")
    residual_ax.set_xlabel("Concentration (ug/mL)")
    residual_ax.set_ylabel("Residual")
    fig.tight_layout()
    fig.savefig(p, dpi=120)
    plt.close(fig)
    return p
