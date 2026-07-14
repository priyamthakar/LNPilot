# Backend contract

LNPilot 0.1.1 exports additive, versioned records for Python, CLI, and UI consumers.
Existing v0.1 fields remain present.

## Common fields

Every top-level record returned by `to_dict()` contains:

- `schema_version`: currently `1.0.0`;
- `record_type`: `batch_plan`, `assay_run`, or `result`;
- `provenance`: software, workflow, method, timestamp, assumptions, warnings, and input identities.

File-backed inputs include their supplied path, resolved path, byte size, and SHA-256 digest.
The UI should display the supplied path and hash, but should not assume a resolved path is portable.

## Batch plan

Stable sections are `target`, `rna`, `lipids`, `stocks`, `aqueous`, `organic`, `mixing`,
`downstream`, `theoretical`, `mass_balance`, `warnings`, `assumptions`, and `provenance`.

`expected_recovery` must be greater than zero and no greater than one. `fill_volume` must be
positive and `n_vials` must be a positive integer.

## Assay run

Stable sections are `plate_map`, `calibration`, `sample_table`, `results`, `qc`, `warnings`,
`assumptions`, and `provenance`.

Plate-map standard concentrations are canonicalized to `ug/mL`. Each normalized well retains
`entered_concentration` and `entered_concentration_unit` for audit display.

The calibration record includes `lloq`, `uloq`, `residual_standard_error`, and
`standard_summary`. Sample rows include replicate SD/CV, encapsulated RNA, EE, and the optional
95% EE interval. Confidence-interval values in `sample_table` are fractions; `Result` confidence
intervals for EE are percentage points.

For one sample, recovery accepts scalar `input_rna_mass` and `sample_volume`. For multiple samples,
both arguments must be mappings keyed by `sample_key`. Recovery fields are added to each applicable
sample row.

## Compatibility policy

Patch releases may add fields but do not remove or rename existing fields. Consumers should ignore
unknown fields. A breaking record change requires a new major `schema_version`.
