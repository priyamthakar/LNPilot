"""Serializable calibration models (no prediction closures in results)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

import numpy as np

from lnpilot.core.exceptions import CalibrationError
from lnpilot.core.validation import require_equal_length, require_finite


@dataclass
class LinearCalibration:
    """y = slope * x + intercept  (y = signal, x = concentration)."""

    slope: float
    intercept: float
    r_squared: float
    n_points: int
    x_min: float
    x_max: float
    residuals: list[float] = field(default_factory=list)
    x_standards: list[float] = field(default_factory=list)
    y_standards: list[float] = field(default_factory=list)
    weighted: bool = False
    model: str = "linear"

    def predict_concentration(self, signal: float) -> float:
        if abs(self.slope) < 1e-15:
            raise CalibrationError("Cannot invert calibration: slope is ~0")
        return (float(signal) - self.intercept) / self.slope

    def predict_signal(self, concentration: float) -> float:
        return self.slope * float(concentration) + self.intercept

    def in_range(self, concentration: float) -> bool:
        return self.x_min <= concentration <= self.x_max

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fit_linear(
    concentrations: Sequence[float],
    signals: Sequence[float],
    *,
    weights: Sequence[float] | None = None,
) -> LinearCalibration:
    """Fit linear calibration; concentrations on x, signals on y."""
    x = np.asarray([require_finite("concentration", float(v)) for v in concentrations], dtype=float)
    y = np.asarray([require_finite("signal", float(v)) for v in signals], dtype=float)
    require_equal_length(list(x), list(y), names=("concentrations", "signals"))
    if len(x) < 2:
        raise CalibrationError("Need at least 2 standard points for linear fit")

    w = None
    if weights is not None:
        w = np.asarray([require_finite("weight", float(v)) for v in weights], dtype=float)
        require_equal_length(list(x), list(w), names=("concentrations", "weights"))
        if np.any(w <= 0):
            raise CalibrationError("Weights must be > 0")

    if w is None:
        # unweighted least squares
        A = np.vstack([x, np.ones(len(x))]).T
        sol, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
        slope, intercept = float(sol[0]), float(sol[1])
        y_hat = slope * x + intercept
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    else:
        # weighted: minimize sum w (y - (sx+i))^2
        sw = np.sum(w)
        swx = np.sum(w * x)
        swy = np.sum(w * y)
        swxx = np.sum(w * x * x)
        swxy = np.sum(w * x * y)
        denom = sw * swxx - swx * swx
        if abs(denom) < 1e-18:
            raise CalibrationError("Degenerate weighted design matrix")
        slope = float((sw * swxy - swx * swy) / denom)
        intercept = float((swy - slope * swx) / sw)
        y_hat = slope * x + intercept
        ss_res = float(np.sum(w * (y - y_hat) ** 2))
        y_bar = swy / sw
        ss_tot = float(np.sum(w * (y - y_bar) ** 2))

    # Relative to signal scale so flat standards always fail
    scale = max(float(np.max(np.abs(y))), 1.0)
    if abs(slope) < 1e-12 * scale and abs(slope) < 1e-9:
        raise CalibrationError("Calibration slope is zero or near-zero")

    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    residuals = (y - y_hat).tolist()

    return LinearCalibration(
        slope=slope,
        intercept=intercept,
        r_squared=r2,
        n_points=len(x),
        x_min=float(np.min(x)),
        x_max=float(np.max(x)),
        residuals=residuals,
        x_standards=x.tolist(),
        y_standards=y.tolist(),
        weighted=w is not None,
    )
