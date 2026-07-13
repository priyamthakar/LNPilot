"""FRR / TFR flow-rate derivation and junction ethanol fraction."""

from __future__ import annotations

import re
from typing import Any

from lnpilot.core.exceptions import ValidationError
from lnpilot.core.validation import require_positive

_FRR_RE = re.compile(
    r"^\s*([\d.]+)\s*:\s*([\d.]+)\s+"
    r"(aqueous\s*:\s*organic|organic\s*:\s*aqueous)\s*$",
    re.IGNORECASE,
)


def parse_frr(frr: str) -> dict[str, Any]:
    """Parse FRR string like '3:1 aqueous:organic' or '1:3 organic:aqueous'.

    Returns aqueous_to_organic volume ratio and convention label.
    """
    if not isinstance(frr, str) or not frr.strip():
        raise ValidationError(
            "frr must be an explicit string such as '3:1 aqueous:organic'"
        )
    m = _FRR_RE.match(frr.strip())
    if not m:
        raise ValidationError(
            "Invalid frr. Use e.g. '3:1 aqueous:organic' or '1:3 organic:aqueous'. "
            "Convention is never inferred silently."
        )
    a, b = float(m.group(1)), float(m.group(2))
    if a <= 0 or b <= 0:
        raise ValidationError("FRR parts must be > 0")
    convention = re.sub(r"\s+", "", m.group(3).lower())
    if convention == "aqueous:organic":
        aq_over_org = a / b
        ratio_a, ratio_b = a, b
    else:  # organic:aqueous — first number is organic
        aq_over_org = b / a
        # store as aqueous:organic parts for clarity
        ratio_a, ratio_b = b, a
        convention = "aqueous:organic"  # normalized storage
        original = "organic:aqueous"
        return {
            "convention": convention,
            "entered_convention": original,
            "entered": frr.strip(),
            "aqueous_parts": ratio_a,
            "organic_parts": ratio_b,
            "aqueous_to_organic": aq_over_org,
        }
    return {
        "convention": "aqueous:organic",
        "entered_convention": "aqueous:organic",
        "entered": frr.strip(),
        "aqueous_parts": ratio_a,
        "organic_parts": ratio_b,
        "aqueous_to_organic": aq_over_org,
    }


def flow_rates_mL_per_min(
    total_flow_rate_mL_per_min: float,
    aqueous_to_organic: float,
) -> dict[str, float]:
    """Derive aqueous and organic flow rates from TFR and aq:org volume ratio.

    TFR = Q_aq + Q_org
    Q_aq / Q_org = r  =>  Q_org = TFR / (r + 1), Q_aq = TFR * r / (r + 1)
    """
    tfr = require_positive("total_flow_rate_mL_per_min", total_flow_rate_mL_per_min)
    r = require_positive("aqueous_to_organic", aqueous_to_organic)
    q_org = tfr / (r + 1.0)
    q_aq = tfr * r / (r + 1.0)
    return {
        "total_flow_rate_mL_per_min": tfr,
        "aqueous_flow_mL_per_min": q_aq,
        "organic_flow_mL_per_min": q_org,
        "aqueous_to_organic": r,
    }


def junction_ethanol_fraction(aqueous_to_organic: float) -> float:
    """Volume fraction of organic (typically ethanol) at the mixing junction.

    Assumes organic phase is the ethanolic lipid stream.
    f_EtOH_junction = Q_org / (Q_aq + Q_org) = 1 / (r + 1)
    This is NOT post-dilution / dialysis / TFF ethanol level.
    """
    r = require_positive("aqueous_to_organic", aqueous_to_organic)
    return 1.0 / (r + 1.0)


def phase_volumes_for_batch(
    total_mixed_volume_mL: float,
    aqueous_to_organic: float,
) -> dict[str, float]:
    """Split total mixed volume into aqueous and organic phase volumes."""
    v = require_positive("total_mixed_volume_mL", total_mixed_volume_mL)
    r = require_positive("aqueous_to_organic", aqueous_to_organic)
    v_org = v / (r + 1.0)
    v_aq = v * r / (r + 1.0)
    return {
        "total_mixed_volume_mL": v,
        "aqueous_volume_mL": v_aq,
        "organic_volume_mL": v_org,
    }


def mixing_time_min(path_volume_mL: float, total_flow_rate_mL_per_min: float) -> float | None:
    """Optional residence/mixing time if a path volume is provided."""
    if path_volume_mL is None:
        return None
    pv = require_positive("path_volume_mL", path_volume_mL)
    tfr = require_positive("total_flow_rate_mL_per_min", total_flow_rate_mL_per_min)
    return pv / tfr
