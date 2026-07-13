import pytest

from lnpilot.core.exceptions import UnitError
from lnpilot.core.units import to_canonical


def test_mass_ug():
    assert to_canonical("100 ug", "mass") == pytest.approx(100.0)
    assert to_canonical("0.1 mg", "mass") == pytest.approx(100.0)


def test_flow():
    assert to_canonical("12 mL/min", "flow") == pytest.approx(12.0)


def test_bad_unit():
    with pytest.raises(UnitError):
        to_canonical("12 foobars", "flow")
