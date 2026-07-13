import pytest

from lnpilot.core.exceptions import ValidationError
from lnpilot.formulate.mixing import flow_rates_mL_per_min, junction_ethanol_fraction, parse_frr


def test_parse_frr_aqueous_organic():
    info = parse_frr("3:1 aqueous:organic")
    assert info["aqueous_to_organic"] == pytest.approx(3.0)


def test_parse_frr_organic_aqueous():
    info = parse_frr("1:3 organic:aqueous")
    assert info["aqueous_to_organic"] == pytest.approx(3.0)


def test_flows_sum_to_tfr():
    f = flow_rates_mL_per_min(12.0, 3.0)
    assert f["aqueous_flow_mL_per_min"] + f["organic_flow_mL_per_min"] == pytest.approx(12.0)
    assert f["aqueous_flow_mL_per_min"] / f["organic_flow_mL_per_min"] == pytest.approx(3.0)


def test_junction_etoh():
    assert junction_ethanol_fraction(3.0) == pytest.approx(0.25)


def test_silent_frr_rejected():
    with pytest.raises(ValidationError):
        parse_frr("3:1")
