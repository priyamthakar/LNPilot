import pytest

from lnpilot.core.exceptions import ValidationError
from lnpilot.formulate.np_ratio import (
    ionizable_lipid_nmol_for_np,
    np_from_amounts,
    rna_phosphate_nmol,
)


def test_phosphate_hand_calc():
    # 330 ug RNA, avg MW 330 → 1000 nmol phosphate
    assert rna_phosphate_nmol(330.0, avg_nt_mw_g_per_mol=330.0) == pytest.approx(1000.0)


def test_np_round_trip():
    p = 100.0
    lipid = ionizable_lipid_nmol_for_np(p, 6.0, ionizable_groups_per_molecule=1.0)
    assert lipid == pytest.approx(600.0)
    assert np_from_amounts(lipid, p) == pytest.approx(6.0)


def test_reject_zero_rna():
    with pytest.raises(ValidationError):
        rna_phosphate_nmol(0.0)
