# TAIVAS Manuscript-to-System Traceability Audit

> **SUPERSEDED STATUS NOTICE (2026-07-22):** This document records the repository
> state before Phase 1 alignment. Its findings are retained for historical
> traceability and must not be interpreted as the current production status.
> The supported entry point now delegates to `core.energy_balance_phase2`.

Audit date: 2026-07-22  
Repository: `C:\Users\USER\Documents\Codex\2026-05-15\streamlit-scenario-logic-ui-1-sidebar`  
Authoritative manuscript audited: `C:\Users\USER\Desktop\TAIVAS_EIA2026_FINAL_SUBMISSION.pdf`  
Manuscript title: *TAIVAS: A Transparent Scenario-Based Energy Resilience Simulator for Extreme-Weather Decision Support*  
Scope: inspection only. No application, test, deployment, or calculation code was modified.

## Executive conclusion

The repository contains a manuscript-aligned deterministic energy-balance implementation in `core/energy_balance_phase2.py`, and the 25 available unit tests validate that module. However, README and deployment instructions still designate `taivas_control_center.py` as the application entry point, and that file does not call the Phase 2 core. Its local `compute_energy_supply()` retains an implicit MW/MWh conversion and a scale-dependent `system_efficiency` formula. Therefore the currently documented deployment path is not fully traceable to the final manuscript.

The audit status is **Partial, with P0 deployment-to-methodology inconsistencies**. The Phase 2 method is present and tested, but it is not the documented production entry point.

## Traceability matrix

| Manuscript requirement | Current implementation evidence | Status | Risk level | Exact file and function | Recommended change | Priority |
|---|---|---|---|---|---|---|
| Product title and positioning as a transparent scenario-based energy resilience simulator | The hero says "Understand Energy Resilience Under Extreme Weather" and calls TAIVAS a scenario-based simulation tool. The page title and I18N title still use "TAIVAS Energy Control Center". | Partial | Medium | `taivas_control_center.py`: `st.set_page_config`, hero rendering near lines 4331-4337, `I18N` | Align the visible product title/subtitle with the manuscript while retaining the TAIVAS name. | P1 |
| Not a forecasting, optimization, validated engineering, or autonomous control system | Methodology, governance, concept boundaries, and exports repeatedly state these limits. Some legacy words remain in internal modules and some export headings. | Partial | Medium | `taivas_control_center.py`: `render_methodology_and_limitations_panel`, `render_research_transparency_panel`, `render_decision_support_notice`; `agent/*.py`; `taivas_utility_toolkit.py` | Keep boundaries and replace remaining visible legacy labels only. Preserve internal identifiers only where compatibility requires them. | P1 |
| Deterministic simulation through explicit calculations | Demand, renewable supply, storage, final supply, energy gap, and risk are explicit arithmetic. Same inputs are repeatable in the Phase 2 tests. | Aligned | Low | `taivas_control_center.py::compute_energy_supply`; `core/energy_balance_phase2.py::compute_energy_supply_core`; `tests/test_energy_balance_phase2.py::test_repeatability` | No architecture rewrite. Select one audited core as the sole execution path. | P0 |
| Separate rule-based interpretation layer | Advisory, diagnostics, monitoring, and workflow functions use thresholds and templates after the simulation result exists. | Aligned | Low | `taivas_control_center.py::generate_agentic_advisory`, `rank_shortfall_drivers`, `generate_diagnostic_recommendations`; `agent/monitoring_layer.py`; `agent/workflow_layer.py` | Keep the layer output-only and document rule thresholds in audit exports. | P1 |
| No runtime machine learning, large language model, external artificial-intelligence API, or generative inference | Repository search found no OpenAI, Anthropic, transformer, TensorFlow, PyTorch, scikit-learn, HTTP inference, or similar runtime call. The transparency panel explicitly states no runtime generative model. | Aligned | Low | `taivas_control_center.py::render_research_transparency_panel`; all Python files searched | Retain the transparency statement. Rename visible "AI" labels where any remain. | P1 |
| Explicit one-hour simulation interval | `SIMULATION_INTERVAL_HOURS = 1.0` exists in the Phase 2 core. The documented entry point does not import or use it. | Contradictory | High | `core/energy_balance_phase2.py::SIMULATION_INTERVAL_HOURS`, `compute_energy_supply_core`; `taivas_control_center.py::compute_energy_supply`; README and deployment commands | Make `taivas_control_center.py` delegate to the Phase 2 core, preserving existing return keys. | P0 |
| Power in MW and battery state/transferred energy in MWh | Phase 2 uses explicit `_mw` and `_mwh` values. Current entry point directly adds `charge` and `discharge` to a battery state without multiplying by interval hours. | Contradictory | High | `core/energy_balance_phase2.py::update_battery_state`; `taivas_control_center.py::compute_energy_supply` lines 973-981 | Replace the entry-point storage block with the audited helper. Do not change parameter values. | P0 |
| Energy transfer equals power multiplied by one-hour interval | Implemented and tested in Phase 2; absent from the documented main path. | Contradictory | High | `core/energy_balance_phase2.py::update_battery_state` lines 75-95; `tests/test_energy_balance_phase2.py::test_one_hour_mw_to_mwh_conversion` | Route production calculations through the tested helper and add an entry-point regression test. | P0 |
| Battery charging, discharge, bounds, and loss | Phase 2 bounds charge by headroom, discharge by stored energy and limit, applies 4% to accepted transfer energy, and bounds state. Tests cover all. Current main has an implicit-unit variant. | Partial | High | `core/energy_balance_phase2.py::update_battery_state`; `taivas_control_center.py::compute_energy_supply`; `tests/test_energy_balance_phase2.py` | Use the Phase 2 helper in the production entry point. | P0 |
| Parameter defaults are author-defined, exploratory, and uncalibrated | `TAIVAS_phase2_parameter_provenance.csv` documents this for all listed parameters. Current Research Mode displays only five parameters and omits evidence status. | Partial | Medium | `TAIVAS_phase2_parameter_provenance.csv`; `taivas_control_center.py::render_research_transparency_panel` | Display the complete provenance table or equivalent fields in Research Mode and include it in audit exports. | P1 |
| Unmet-demand ratio is energy gap divided by demand | Explicit in Phase 2. Current main computes the same percentage under `grid_dependency` but does not return an explicit `unmet_demand_ratio`. | Partial | Medium | `core/energy_balance_phase2.py::compute_energy_supply_core`; `taivas_control_center.py::compute_energy_supply` lines 991-998 | Preserve the legacy alias but add and use the explicit field. | P0 |
| System Performance Score is percentage of modeled demand served | Phase 2 implements `100 * (1 - gap/demand)` and handles zero demand as not applicable. Current main uses `100 - shortfall * 0.55`, which depends on MW scale. | Contradictory | High | `core/energy_balance_phase2.py::calculate_system_performance_score`; `taivas_control_center.py::compute_energy_supply` line 997 | Route to Phase 2 and make the visible label System Performance Score. | P0 |
| System Performance Score is not efficiency, reliability, or regulatory resilience | Current main and toolkit still display "System Efficiency", "System Stability", and related labels in cards and exports. | Contradictory | High | `taivas_control_center.py::scenario_comparison_metrics`, `compare_baseline_vs_scenario`, `build_executive_summary_text`, `generate_simulation_report_text`; `taivas_utility_toolkit.py` | Replace only user-facing/export labels with System Performance Score and add its definition. | P0 |
| External Support Need Proxy is not measured imported grid electricity | The Phase 2 core defines the proxy correctly. Current main numerically computes the same percentage as `grid_dependency`, but visible labels alternate among Grid Dependency, Backup Grid Need, and Need for External Power. | Partial | High | `core/energy_balance_phase2.py::compute_energy_supply_core`; `taivas_control_center.py::scenario_comparison_metrics`, `compare_baseline_vs_scenario`; toolkit exporters | Keep the legacy key for compatibility, but display only External Support Need Proxy with the non-import disclaimer. | P0 |
| Risk tiers: Low, Elevated, High, Critical using exploratory 5% and 15% thresholds | Core risk engine and tests match the manuscript. The scenario panel displays "Moderate" for the under-5% tier. | Contradictory | Medium | `core/risk_engine.py::calculate_risk_tier`; `taivas_control_center.py::operational_risk_tier_for_display`; `tests/test_risk_engine.py` | Use the core risk-tier value for display and label thresholds exploratory. | P1 |
| Normal is the baseline | Baseline calculation uses `normal`, zero component-failure ratios, and zero recovery lag. | Aligned | Low | `taivas_control_center.py` baseline construction near lines 3399-3409 | Keep the baseline path and include its exact assumptions in exports. | P1 |
| Baseline-versus-stress comparison covers all required outputs | Demand, renewable supply, final supply, gap, battery state, renewable share, support proxy, and score are compared. Battery contribution and risk-tier delta are not included in the same comparison structure. | Partial | Medium | `taivas_control_center.py::scenario_comparison_metrics`, `compare_baseline_vs_scenario` | Add battery contribution and risk tier to the comparison without changing calculations. | P1 |
| Deterministic exploratory output, not observed data or historical validation | Research transparency and method sections state the boundary; data-source labels distinguish public/user/simulated data. | Aligned | Low | `taivas_control_center.py::render_methodology_and_limitations_panel`, `render_research_transparency_panel` | Keep these notices visible in Beginner Mode and exports. | P1 |
| Not a forecast or guaranteed prediction; not authorization for action; human review required | Strong notices are present in dashboard, advisory, governance, diagnostics, and report text. | Aligned | Low | `taivas_control_center.py::render_decision_support_notice`, `render_human_in_loop_panel`, `render_agentic_advisory_layer`, `generate_simulation_report_text` | Retain wording; check every exporter for the same disclaimer. | P1 |
| Beginner and advanced views use the same simulation engine | Both views render from the same global `results` and `baseline_results`; mode changes presentation density only. | Aligned | Low | `taivas_control_center.py` sidebar Beginner Mode and bottom Overview/Advanced Analysis rendering | Add a small regression test or static assertion that mode selection does not enter calculation code. | P2 |
| Advanced view exposes assumptions, diagnostics, provenance, comparisons, and exports | Advanced tabs include methodology, research transparency, governance/audit, export, diagnostics, and scenario views. Provenance detail is incomplete in the current entry point. | Partial | Medium | `taivas_control_center.py` advanced tabs near lines 6885-6908; `render_research_transparency_panel` | Complete the provenance table and audit payload. | P1 |
| Battery-capacity versus demand-assumption sensitivity analysis | Offline builder runs 3 battery multipliers by 3 demand multipliers for Blizzard and exports all nine rows. It shows energy gap, score, and risk tier. The app does not provide an equivalent live sensitivity view. | Aligned for manuscript artifact; Partial for product UI | Low | `build_taivas_phase2_artifacts.py::build_analysis_csvs`, `build_figure3`; `TAIVAS_phase2_sensitivity_analysis.csv` | No calculation change. Optionally expose the existing generated artifact in Research Mode later. | P2 |
| Sensitivity multipliers are not probabilities or calibrated uncertainty bounds | Figure-generation note and manuscript builder state this explicitly. | Aligned | Low | `build_taivas_phase2_artifacts.py::build_figure3` | Retain the boundary in any future UI exposure. | P2 |
| Audit export contains all inputs and outputs, scenario, timestamp, and boundary | Audit record includes final inputs, failure ratios, location, selected/baseline/timeline outputs, interpretation structures, timestamp, and model boundary. | Aligned | Low | `taivas_control_center.py::build_audit_trail_record`; `export/audit_export.py::audit_record_to_json` | Retain existing fields. | P1 |
| Audit export contains scenario multipliers, parameter values/units/evidence, interval, model version, rules, and overrides | Current audit omits the actual multiplier snapshot, full parameter provenance, explicit interval, audited code hash/version, rule definitions, and structured override deltas. | Missing | High | `taivas_control_center.py::build_audit_trail_record` | Add a versioned `model_manifest` and `parameter_manifest` while preserving legacy keys. | P0 |
| Exported reports use manuscript-safe indicator names | TXT, executive summary, PDF/PPT utility, and some tables still use System Efficiency, Grid Dependency, Battery Stability, and Recommendation. | Contradictory | High | `taivas_control_center.py::build_executive_summary_text`, `generate_simulation_report_text`; `taivas_utility_toolkit.py` PDF/PPT builders | Update labels and definitions only; do not rename result keys. | P0 |
| Software tests cover listed behaviors | 25 tests cover validation, risk tiers, minimal audit schema, scenario compatibility, battery bounds/charge/discharge/one-hour conversion/loss, repeatability, score normalization/scale invariance, and zero demand. | Aligned for Phase 2 module | Low | `tests/test_*.py` | Keep tests and add production-entrypoint parity tests. | P0 |
| Tests verify the code path designated for deployment | Energy tests import `core.energy_balance_phase2`, while README deploys `taivas_control_center.py`, which has a separate implementation. | Missing | High | `tests/test_energy_balance_phase2.py`; `README.md`; `DEPLOYMENT_PORTABILITY.md`; `taivas_control_center.py` | Add a test that the production wrapper delegates to or equals the audited core. | P0 |
| Repository can start from its documented entry point | Requirements lists external packages, but this repository lacks `modules/` and `concept_lab_components.py`, both imported by the main files. | Contradictory | High | `taivas_control_center.py` lines 22-25 and 108; `taivas_control_center_PHASE2.py` lines 22-31 and 113; repository tree | Restore the exact deployed modules from source control or change imports only after confirming the canonical deployment repository. | P0 |

## Parameter provenance matrix

Unless repository evidence says otherwise, every default below is treated as **author-defined, exploratory, and uncalibrated**.

| Parameter | Current value and unit | Code location and function | User-facing label / visibility | Editable | User override logged | Audit finding |
|---|---|---|---|---|---|---|
| Demand coefficient | `0.000035 MW/person` | `taivas_control_center.py:866`; passed to `core/energy_balance_phase2.py::compute_energy_supply_core` only by the Phase 2 wrapper | "Demand per capita" in current Research Mode | No | No override available; value not snapshotted in audit | Provenance exists only in companion CSV; current production path lacks manifest export. |
| Facility factors | Long-term Care 1.12; Hospital 1.22; Data Center 1.18; School/Campus 0.92; Residential 0.88; ratio | `taivas_control_center.py:872-878`; `facility_demand_factor` | User selects Facility Type, but numeric factor is not shown | Facility choice yes; factor no | Facility choice logged; resolved factor not logged | Partial traceability. |
| Solar coefficient | `0.58`, ratio | `taivas_control_center.py:867`; `compute_energy_supply` | "Solar efficiency" visible in Research Mode | No | No | Label can imply empirical efficiency although it is an exploratory coefficient. |
| Wind coefficient | `0.42`, ratio | `taivas_control_center.py:868`; `compute_energy_supply` | "Wind efficiency" visible in Research Mode | No | No | Same provenance issue as solar. |
| Geothermal availability | `0.85`, ratio | `taivas_control_center.py:869`; `compute_energy_supply` | "Geothermal availability" visible in Research Mode | No | No | Provenance CSV correctly marks uncalibrated. |
| Hydropower rule | `clamp(0.45 + precipitation/500 * 0.35, 0.15, 0.95)`, ratio | `taivas_control_center.py:953`; `core/energy_balance_phase2.py:146` | Not shown in current Research Mode | No | No | Missing from current UI and audit payload. |
| Battery charge share | `0.30`, ratio of surplus per interval | Hard-coded in current main line 976; `core/energy_balance_phase2.py:16`, `update_battery_state` | Not visible | No | No | Present in provenance CSV only. |
| Battery dispatch-capacity share | `0.35`, ratio per interval | Hard-coded in current main line 977; `core/energy_balance_phase2.py:17`, `update_battery_state` | Not visible | No | No | Present in provenance CSV only. |
| Battery transfer loss | `0.04`, ratio | `taivas_control_center.py:870`; Phase 2 `update_battery_state` | "Battery round-trip loss" visible in Research Mode | No | No | Current main applies it to implicitly dimensioned transfer; Phase 2 applies it to MWh. |
| Simulation interval | `1.0 h` in Phase 2 only | `core/energy_balance_phase2.py:15`, `update_battery_state` | Not visible in documented production entry point | No | No | P0 entry-point mismatch. |
| Scenario multipliers | Six fixed dictionaries: Normal, Heat Wave, Storm, Cold Wave, Blizzard, Typhoon | `taivas_control_center.py::SCENARIOS`; used by `compute_energy_supply` | Scenario-factor table visible in Research Mode | Scenario selected; values not editable | Scenario name logged; multiplier snapshot not logged | Values are uncalibrated and should be exported with each run. |
| Risk thresholds | Low no gap; Elevated under 5%; High 5%-under 15%; Critical at least 15% | `core/risk_engine.py::calculate_risk_tier` | Generic risk caption; selected display changes Elevated to Moderate | No | No | Core is manuscript-aligned; display is not. |

## Five highest-risk inconsistencies

1. **P0 - Production entry point does not use the audited Phase 2 core.** README and deployment docs run `taivas_control_center.py`; the manuscript-aligned wrapper is in `taivas_control_center_PHASE2.py`.
2. **P0 - System Performance Score is wrong in the documented main path.** It uses `100 - shortfall * 0.55`, not percentage of demand served.
3. **P0 - MW/MWh conversion is implicit in the documented main path.** The tested one-hour conversion exists only in the Phase 2 core path.
4. **P0 - Green tests do not prove production-path parity.** All energy-balance unit tests target `core.energy_balance_phase2`, not the deployed wrapper named in README.
5. **P0 - The audited repository is not self-contained.** `modules/` and `concept_lab_components.py` are imported but absent, so a clean deployment from this folder cannot reach the app after dependencies are installed.

## Minimal-change implementation plan

1. Make `taivas_control_center.py::compute_energy_supply` a thin wrapper around `core.energy_balance_phase2.compute_energy_supply_core`, following the already-existing Phase 2 wrapper. Preserve all legacy output keys.
2. Add a production-path parity test that calls the documented wrapper without rendering Streamlit and compares it with the core for Normal, Blizzard, zero battery, full battery, and zero-demand helper behavior.
3. Replace user-facing and export labels only: System Performance Score, External Support Need Proxy, Battery Remaining. Use the core risk tier value, including Elevated.
4. Extend `build_audit_trail_record()` with a versioned model manifest containing parameter values, units, evidence status, scenario multipliers, interval, risk thresholds, code version/hash, and explicit user overrides. Preserve existing keys.
5. Restore the missing canonical `modules/` package and `concept_lab_components.py` from the actual deployed repository, then run a clean-environment Streamlit smoke test.
6. Complete current Research Mode provenance rows using the existing companion provenance CSV or a code-level constant manifest.

## Files that would be modified after approval

- `taivas_control_center.py`
- `taivas_utility_toolkit.py`
- `README.md` and `DEPLOYMENT_PORTABILITY.md` only if entry-point wording needs clarification
- `tests/test_energy_balance_phase2.py` or a new `tests/test_production_entrypoint.py`
- `tests/test_audit_export.py`
- A new label/export regression test, such as `tests/test_manuscript_terminology.py`
- Missing canonical files to restore, if confirmed: `modules/charts.py`, `modules/recommendations.py`, `modules/energy_security.py`, `modules/survival_timeline.py`, `concept_lab_components.py`

The following should not require formula changes: `CITY_DATA`, `FACILITY_PROFILES`, `SCENARIOS`, energy-security logic, geopolitical logic, survival-timeline logic, CSV processing, and deployment environment settings.

## Tests to add or update

- Production entry-point to Phase 2 core parity for all six scenarios.
- Explicit one-hour MW-to-MWh conversion through the documented entry point.
- Production-path battery bounds, full/empty state, charging, discharge, and transfer loss.
- System Performance Score equals percentage of demand served and is scale invariant through the documented entry point.
- Zero-demand score is not applicable without a crash.
- Visible/exported terminology contains System Performance Score and External Support Need Proxy and excludes misleading legacy labels.
- Risk display preserves Elevated rather than converting it to Moderate.
- Audit manifest includes all parameters, units, evidence status, scenario multipliers, interval, rule thresholds, version/hash, timestamp, and user overrides.
- Clean-import smoke test with all required repository modules present.

## Exact verification results

Commands executed with the bundled Python runtime:

- `python -m py_compile taivas_control_center.py`: **passed**.
- `python -m py_compile taivas_control_center_PHASE2.py core/energy_balance_phase2.py`: **passed**.
- `python -m unittest discover -s tests -v`: **25 discovered, 25 passed, 0 failed, 0 skipped**.

Coverage represented by those 25 tests:

- Data validation: 3.
- Audit export minimum schema: 1.
- Risk tiers: 4.
- Scenario compatibility: 6.
- Phase 2 battery and indicator behavior: 11, including bounds, charge, discharge, explicit one-hour conversion, loss, repeatability, scale-invariant scoring, and zero-demand handling.

Important boundary: these software tests demonstrate specified code behavior only. They do not establish numerical calibration, historical validity, predictive accuracy, or real-world infrastructure resilience.

## Runtime verification limitation

The bundled Python runtime used for this audit does not have `matplotlib` installed, so importing the Streamlit main file stops before application rendering. That environment issue is separate from the repository issue. Static repository inspection also confirms that `modules/` and `concept_lab_components.py` are absent even though both main files import them. A successful syntax compile therefore must not be reported as a successful application startup.

## Manuscript visual/source check

The attached PDF contains 11 pages. It was text-extracted and rendered page by page for visual inspection. The manuscript consistently defines the deterministic, one-hour, rule-based, human-reviewed boundaries used in this audit. No code was changed as part of this comparison.
