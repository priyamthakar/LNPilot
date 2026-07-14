"""Provenance records for reproducible outputs."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _pkg_version() -> str:
    try:
        from importlib.metadata import version

        return version("lnpilot")
    except Exception:
        return "0.1.1"


def source_file_record(role: str, path: str | Path) -> dict[str, Any]:
    """Create a stable identity record for an input file."""
    source = Path(path)
    resolved = source.resolve()
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return {
        "role": role,
        "path": str(source),
        "resolved_path": str(resolved),
        "size_bytes": resolved.stat().st_size,
        "sha256": digest.hexdigest(),
    }


@dataclass
class Provenance:
    software_name: str = "LNPilot"
    software_version: str = ""
    workflow_name: str = ""
    workflow_version: str = "0.1.1"
    generated_at: str = ""
    source_files: list[dict[str, Any]] = field(default_factory=list)
    operator: str | None = None
    method_id: str | None = None
    equations_version: str = "0.1.1"
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    instrument_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.software_version:
            self.software_version = _pkg_version()
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(
        cls,
        workflow_name: str,
        *,
        software_version: str | None = None,
        assumptions: list[str] | None = None,
        warnings: list[str] | None = None,
        source_files: list[dict[str, Any]] | None = None,
        operator: str | None = None,
        method_id: str | None = None,
        **kwargs: Any,
    ) -> Provenance:
        return cls(
            software_version=software_version or _pkg_version(),
            workflow_name=workflow_name,
            assumptions=list(assumptions or []),
            warnings=list(warnings or []),
            source_files=list(source_files or []),
            operator=operator,
            method_id=method_id,
            **kwargs,
        )
