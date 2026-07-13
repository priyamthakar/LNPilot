import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lnpilot.formulate.mixing import flow_rates_mL_per_min
from lnpilot.formulate.np_ratio import ionizable_lipid_nmol_for_np, np_from_amounts


@given(
    tfr=st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False),
    r=st.floats(min_value=0.1, max_value=20, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50)
def test_flows_sum_property(tfr, r):
    f = flow_rates_mL_per_min(tfr, r)
    assert f["aqueous_flow_mL_per_min"] + f["organic_flow_mL_per_min"] == pytest.approx(
        tfr, rel=1e-9, abs=1e-9
    )


@given(
    p=st.floats(min_value=1e-3, max_value=1e6, allow_nan=False, allow_infinity=False),
    np_ratio=st.floats(min_value=0.1, max_value=50, allow_nan=False, allow_infinity=False),
    g=st.floats(min_value=0.1, max_value=5, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50)
def test_np_roundtrip_property(p, np_ratio, g):
    lipid = ionizable_lipid_nmol_for_np(p, np_ratio, ionizable_groups_per_molecule=g)
    assert np_from_amounts(lipid, p, ionizable_groups_per_molecule=g) == pytest.approx(
        np_ratio, rel=1e-9, abs=1e-9
    )
