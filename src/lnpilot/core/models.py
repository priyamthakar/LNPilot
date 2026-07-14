"""Minimal typed records for v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from lnpilot.core.provenance import Provenance

RECORD_SCHEMA_VERSION = "1.0.0"


@dataclass
class Result:
    name: str
    value: float | None
    unit: str
    uncertainty: float | None = None
    confidence_interval: tuple[float, float] | None = None
    replicate_count: int | None = None
    method: str | None = None
    qc_status: str = "ok"  # ok | warning | fail
    warnings: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    provenance: Provenance | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = RECORD_SCHEMA_VERSION
        d["record_type"] = "result"
        if self.confidence_interval is not None:
            d["confidence_interval"] = list(self.confidence_interval)
        if self.provenance is not None:
            d["provenance"] = self.provenance.to_dict()
        return d


@dataclass
class BatchPlan:
    batch_id: str
    target: dict[str, Any]
    rna: dict[str, Any]
    lipids: list[dict[str, Any]]
    stocks: list[dict[str, Any]]
    aqueous: dict[str, Any]
    organic: dict[str, Any]
    mixing: dict[str, Any]
    downstream: dict[str, Any]
    theoretical: dict[str, Any]
    mass_balance: dict[str, Any]
    calculation_trace: list[str]
    warnings: list[str]
    assumptions: list[str]
    provenance: Provenance

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = RECORD_SCHEMA_VERSION
        d["record_type"] = "batch_plan"
        d["provenance"] = self.provenance.to_dict()
        return d


@dataclass
class AssayRun:
    assay_id: str
    assay_type: str
    batch_ids: list[str]
    raw_data_ref: str | None
    plate_map: dict[str, Any]
    calibration: dict[str, Any]
    dilution_scheme: dict[str, Any]
    replicates: dict[str, Any]
    reagent_metadata: dict[str, Any]
    qc: dict[str, Any]
    results: list[Result]
    sample_table: list[dict[str, Any]]
    warnings: list[str]
    assumptions: list[str]
    provenance: Provenance

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = RECORD_SCHEMA_VERSION
        d["record_type"] = "assay_run"
        d["provenance"] = self.provenance.to_dict()
        d["results"] = [r.to_dict() if isinstance(r, Result) else r for r in self.results]
        return d
