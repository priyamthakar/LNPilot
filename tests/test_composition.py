import pytest

from lnpilot.core.exceptions import ValidationError
from lnpilot.formulate.composition import (
    component_amounts,
    normalize_composition,
    total_lipid_nmol_from_ionizable,
)


def test_normalize_sums_100():
    comps = normalize_composition(
        [
            {"name": "A", "role": "ionizable", "mol_percent": 50, "mw": 700, "ionizable_groups": 1},
            {"name": "B", "role": "helper", "mol_percent": 50, "mw": 800},
        ]
    )
    assert sum(c["normalized_mol_percent"] for c in comps) == pytest.approx(100.0)


def test_duplicate_names():
    with pytest.raises(ValidationError):
        normalize_composition(
            [
                {"name": "A", "role": "ionizable", "mol_percent": 50, "mw": 700},
                {"name": "A", "role": "helper", "mol_percent": 50, "mw": 800},
            ]
        )


def test_component_nmol_sum():
    comps = normalize_composition(
        [
            {"name": "ion", "role": "ionizable", "mol_percent": 50, "mw": 700, "ionizable_groups": 1},
            {"name": "h", "role": "helper", "mol_percent": 50, "mw": 800},
        ]
    )
    total = total_lipid_nmol_from_ionizable(100.0, comps[0]["mol_fraction"])
    amounts = component_amounts(comps, total)
    assert sum(a["amount_nmol"] for a in amounts) == pytest.approx(total)
