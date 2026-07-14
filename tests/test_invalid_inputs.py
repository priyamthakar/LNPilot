import pytest

from lnpilot import plan_batch
from lnpilot.characterize.plate_map import load_plate_map
from lnpilot.core.exceptions import PlateMapError, ValidationError
from lnpilot.formulate.mixing import parse_frr


def test_zero_mol_percent_component():
    with pytest.raises(ValidationError):
        plan_batch(
            rna_mass="10 ug",
            target_np=6,
            lipid_composition={
                "ionizable": {"mol_percent": 0, "mw": "700 g/mol"},
                "helper": {"mol_percent": 100, "mw": "800 g/mol"},
            },
            frr="3:1 aqueous:organic",
            total_flow_rate="12 mL/min",
        )


def test_bad_frr():
    with pytest.raises(ValidationError):
        parse_frr("aqueous heavy")


def test_dup_wells():
    with pytest.raises(PlateMapError):
        load_plate_map(
            [
                {"well": "A1", "role": "blank"},
                {"well": "A1", "role": "standard", "concentration": "1"},
            ]
        )


def test_plate_map_converts_concentration_units():
    rows = load_plate_map(
        [
            {"well": "A1", "role": "standard", "concentration": 250, "concentration_unit": "ng/mL"},
            {"well": "A2", "role": "standard", "concentration": 1, "concentration_unit": "ug/mL"},
        ]
    )
    assert rows[0]["concentration"] == pytest.approx(0.25)
    assert rows[0]["concentration_unit"] == "ug/mL"
    assert rows[0]["entered_concentration"] == 250
    assert rows[0]["entered_concentration_unit"] == "ng/mL"


def test_plate_map_rejects_incompatible_concentration_units():
    with pytest.raises(PlateMapError):
        load_plate_map(
            [{"well": "A1", "role": "standard", "concentration": 1, "concentration_unit": "mL"}]
        )
