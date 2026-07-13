import pytest

from lnpilot.characterize.calibration import fit_linear
from lnpilot.core.exceptions import CalibrationError


def test_perfect_line():
    # y = 2x + 1
    x = [0, 1, 2, 4]
    y = [1, 3, 5, 9]
    cal = fit_linear(x, y)
    assert cal.slope == pytest.approx(2.0)
    assert cal.intercept == pytest.approx(1.0)
    assert cal.r_squared == pytest.approx(1.0)
    assert cal.predict_concentration(5.0) == pytest.approx(2.0)


def test_zero_slope():
    with pytest.raises(CalibrationError):
        fit_linear([1, 2, 3], [5, 5, 5])


def test_serializable():
    cal = fit_linear([0, 1, 2], [0, 1, 2])
    d = cal.to_dict()
    assert "slope" in d and "predict" not in str(d)
