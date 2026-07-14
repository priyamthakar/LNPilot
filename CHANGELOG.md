# Changelog

## 0.1.1 - 2026-07-13

### Scientific correctness

- Convert plate-map standard concentrations to canonical `ug/mL` and retain entered values.
- Reject recovery fractions above one, non-positive fill volumes, and non-integer vial counts.
- Calculate recovery per sample and require keyed mappings for multi-sample assays.
- Add standard back-calculation, bias, replicate CV, sample CV, LLOQ/ULOQ, and residual diagnostics.
- Add delta-method standard errors and 95% confidence intervals for encapsulation efficiency.

### Reproducibility and integration

- Add SHA-256 identities for file-backed inputs.
- Add `schema_version` and `record_type` to machine-readable records.
- Accept reagent and instrument metadata in backend workflows.
- Add a documented backend contract for UI consumers.
- Add calibration residual plots and richer assay reports.

### Quality gates

- Add MyPy type checking, an 80% coverage floor, distribution builds, and wheel smoke tests to CI.

## 0.1.0 - 2026-07-13

- Initial batch-planning and RiboGreen-analysis workflows.
