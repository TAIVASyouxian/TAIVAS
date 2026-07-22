# TAIVAS Phase 1 Manuscript-System Alignment Change Report

## Executive Summary

The documented application entry point remains `taivas_control_center.py` and
now delegates its energy-balance calculation to the single authoritative,
framework-independent implementation in `core/energy_balance_phase2.py`.
The official calculation path uses an explicit one-hour interval, MW for power,
MWh for battery state and transfers, the manuscript-defined System Performance
Score, and the existing author-defined Risk Tier thresholds.

No runtime machine learning model, large language model, external artificial
intelligence service, empirical calibration evidence, or validation claim was
added.

## P0 Resolution Table

| P0 issue | Previous behavior | Corrected behavior | Modified files | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| Official entry point | `taivas_control_center.py` contained an independent energy-balance implementation. | The documented entry point calls `compute_energy_supply_core()` from `core/energy_balance_phase2.py`. Historical application snapshots are documented as non-official. | `taivas_control_center.py`, `README.md`, `DEPLOYMENT_PORTABILITY.md` | AST integration test plus six-scenario output equality test. | Resolved |
| System Performance Score | `clamp(100 - shortfall_MW * 0.55, 0, 100)`. | `100 * clamp(1 - clamp(gap_MW / demand_MW, 0, 1), 0, 1)`; zero demand returns `None` and displays as Not applicable. | `taivas_control_center.py`, `core/energy_balance_phase2.py`, `taivas_utility_toolkit.py` | Full, partial, no-supply, oversupply, negative-gap, zero-demand, and scale-invariance tests. | Resolved |
| Storage units | MW charge/discharge values were directly added to or subtracted from an MWh battery state. | Transfer energy is explicitly `transfer_power_MW * 1.0 h`; state, capacity, charge, discharge, and loss energy use MWh. | `taivas_control_center.py`, `core/energy_balance_phase2.py` | Charge, discharge, loss, empty/full/zero-capacity, bounds, limits, repeatability, and MW-to-MWh tests. | Resolved |
| Official path verification | Tests covered helpers but did not prove official-entrypoint parity. | Tests execute the exact official wrapper function parsed from `taivas_control_center.py` and compare every scenario with direct core output. | `tests/test_official_entrypoint_alignment.py`, `tests/test_energy_balance_phase2.py` | Helsinki Hospital Blizzard fixture and all six scenarios pass. | Resolved |
| Repository completeness | Missing historical `modules/` and `concept_lab_components.py` imports could stop startup. | Imports are guarded, absence is reported, the deterministic core remains available, and no replacement scientific logic is fabricated. | `taivas_control_center.py`, `README.md` | Compilation succeeds; missing extensions are explicitly classified. | Resolved with optional extensions unavailable |
| Terminology and model boundary | User-facing labels mixed efficiency, stability, and grid-dependency terminology. | Visible and exported primary indicators use System Performance Score, External Support Need Proxy, and Risk Tier with manuscript definitions. The exact deterministic-output boundary is visible and exported. | `taivas_control_center.py`, `taivas_utility_toolkit.py`, `agent/monitoring_layer.py` | Source terminology search and compilation. | Resolved for official path |

## Exact Formula Changes

### System Performance Score

Before:

```text
system_efficiency = clamp(100 - shortfall_MW * 0.55, 0, 100)
```

After, for positive modeled demand:

```text
unmet_demand_ratio = clamp(possible_energy_gap_MW / modeled_demand_MW, 0, 1)
served_demand_ratio = clamp(1 - unmet_demand_ratio, 0, 1)
system_performance_score = 100 * served_demand_ratio
```

For zero modeled demand, the internal value is `None` and the user-facing value
is `Not applicable`.

### Battery State

Before:

```text
battery_next = clamp(
    battery_current_MWh + charge_MW - discharge_MW - loss,
    0,
    battery_capacity_MWh,
)
```

After:

```text
simulation_interval_hours = 1.0
charge_energy_MWh = charge_power_MW * simulation_interval_hours
discharge_energy_MWh = discharge_power_MW * simulation_interval_hours
loss_energy_MWh = (charge_energy_MWh + discharge_energy_MWh) * loss_rate
battery_next_MWh = clamp(
    battery_current_MWh + charge_energy_MWh - discharge_energy_MWh - loss_energy_MWh,
    0,
    battery_capacity_MWh,
)
```

The existing 30% surplus charge share, 35% battery-capacity dispatch limit,
scenario battery factor, availability factor, lag penalty, and 4% loss rate were
not changed.

### Disabled Geopolitical Extension

An integration defect was isolated: event `None` previously reduced battery
state by `energy_gap * 0.08` even though no geopolitical penalty was active.
The disabled extension is now a pass-through. Active geopolitical coefficients
and constants were not changed. When active, its retained 8% stress convention
is expressed dimensionally as:

```text
stress_energy_MWh = adjusted_gap_MW * 1.0 h * 0.08
```

## Official Launch Command

```bash
streamlit run taivas_control_center.py
```

## Modified Files

- `taivas_control_center.py`
- `core/energy_balance_phase2.py`
- `agent/monitoring_layer.py`
- `taivas_utility_toolkit.py`
- `tests/test_energy_balance_phase2.py`
- `tests/test_official_entrypoint_alignment.py`
- `README.md`
- `DEPLOYMENT_PORTABILITY.md`
- `TAIVAS_PHASE1_ALIGNMENT_CHANGE_REPORT.md`

## Verification Results

- Python runtime: 3.12.13
- Modified Python files compiled: pass
- Tests discovered: 37
- Tests passed: 37
- Tests failed: 0
- Tests skipped: 0
- Six official scenarios equal direct authoritative-core outputs: pass
- Helsinki Hospital Blizzard manuscript fixture: pass
- Official-path legacy `0.55` formula search: no match
- `CITY_DATA`, `FACILITY_PROFILES`, and `SCENARIOS` AST comparison against the pre-change compatibility snapshot: unchanged
- CSV parsing functions: unchanged
- Geopolitical event calculation and numerical event constants: unchanged

## Dependency and Launch Verification

`requirements.txt` already declares the required third-party packages, including
Streamlit, pandas, Matplotlib, spreadsheet, image, PDF, and presentation
dependencies. The bundled verification runtime contained pandas and document
libraries but did not contain Streamlit, Matplotlib, or xlrd. Installation into
a temporary directory was attempted and failed because this execution
environment cannot connect to PyPI (`WinError 10013`).

Therefore:

- static compilation: passed;
- numerical and integration tests: passed;
- dependency declaration review: passed;
- live clean Streamlit launch in this restricted environment: blocked by
  unavailable packages and blocked package-network access;
- after-change runtime screenshots: pending deployment or execution in an
  environment where `pip install -r requirements.txt` is available.

This is an environmental blocker, not a claimed application-launch pass.

## Search Evidence

The official main/core/agent/toolkit path contains no legacy `0.55` score
formula. Remaining `0.55` matches elsewhere are historical comparison artifacts,
CSS spacing/opacity values, or unrelated geopolitical input assumptions. They
were inspected and not removed indiscriminately.

The utility toolkit retains `System Stability (%)` and `System Efficiency` only
as legacy input-key fallbacks when reading older scenario-comparison records;
the generated PDF/PPT heading is `System Performance Score`.

All primary battery-capacity and battery-state outputs identify MWh. Power
balance outputs identify MW. The result view and audit export identify the
one-hour simulation interval.

## Model Boundary

> Deterministic exploratory output only. Parameters may be author-defined and
> uncalibrated. This output is not observed data, historical validation, a
> forecast, or authorization for operational action. Human review is required.

## Remaining Limitations

1. Live launch and after-change screenshots require a runtime with the declared
   dependencies installed; this environment could not download them.
2. Historical compatibility snapshots still contain obsolete formulas and are
   deliberately documented as non-official. They should not be used as launch
   entry points.
3. Historical optional extensions under `modules/` and the Concept Lab component
   are absent from this repository snapshot. Their absence is non-fatal and
   explicitly disclosed; no substitute scientific calculations were invented.
4. Parameter calibration, observational validation, sensitivity analysis, and
   broader provenance work remain outside Phase 1.
