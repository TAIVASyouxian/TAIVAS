# TAIVAS Energy Resilience Decision-Support Simulator

TAIVAS is a Streamlit-based energy resilience decision-support simulation tool.

It is not a disaster prediction system, not an automatic emergency command system,
and not a guaranteed forecasting engine.

## Sole Supported Entry Point

Run the app with:

```bash
streamlit run taivas_control_center.py
```

The sole supported application entry point is:

```text
taivas_control_center.py
```

This documented entry point delegates its energy-balance calculation to the
single authoritative deterministic core:

```text
core/energy_balance_phase2.py
```

The core uses an explicit one-hour simulation interval, MW for power, MWh for
battery state and transfers, and defines System Performance Score as the
percentage of modeled demand served.

`taivas_control_center_PHASE2.py` is retained as a compatibility reference and
is not a supported application entry point. Legacy snapshots under
`archive/legacy/` use non-executable extensions and are historical records only;
they must not be executed, imported, deployed, or used for research results.

`core.energy_balance_phase2` is the authoritative manuscript-aligned
energy-balance core used by the supported entry point.

## Folder Structure

```text
.
├── taivas_control_center.py
├── taivas_utility_toolkit.py
├── requirements.txt
├── README.md
├── DEPLOYMENT_PORTABILITY.md
├── .env.example
├── agent/
│   ├── monitoring_layer.py
│   └── workflow_layer.py
├── core/
│   ├── risk_engine.py
│   └── scenario_compatibility.py
├── data/
│   ├── csv_loader.py
│   └── validation_utils.py
├── export/
│   ├── audit_export.py
│   └── markdown_export.py
├── samples/
│   └── taivas_sample_input.csv
└── tests/
```

## Optional Extensions

The repository snapshot may not include the historical `modules/` package or
`concept_lab_components.py`. The official app treats these as optional
presentation/advisory extensions and reports their absence without changing the
authoritative energy-balance result. No replacement scientific logic is
fabricated when they are unavailable.

## Installation

Create a virtual environment if desired, then install dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
streamlit run taivas_control_center.py
```

## Streamlit Cloud Deployment

Use the same main file:

```text
taivas_control_center.py
```

No absolute local paths are required. Generated files are created in memory and
downloaded through Streamlit download buttons.

## TAIVAS Utility Toolkit

The app includes a `TAIVAS Utility Toolkit` tab with:

1. Excel to TAIVAS CSV
2. CSV Validator
3. PDF / PPT Report Generator
4. Image Converter
5. Batch Renamer

The toolkit is designed to be portable:

- It does not write permanent output files to the server.
- It does not require machine-specific local folders.
- It uses uploaded files and in-memory downloads.
- It can run locally or on Streamlit Cloud with the same code.

## Sample Input

A small sample CSV is available at:

```text
samples/taivas_sample_input.csv
```

You can use it with the CSV Validator or as a reference for Excel-to-CSV columns.

Recommended TAIVAS input columns:

```text
timestamp
country
city
lat
lon
temperature
wind_speed
solar_radiation
precipitation
humidity
population
solar_capacity
wind_capacity
geothermal_capacity
hydro_capacity
battery_capacity
```

## Portability Notes

This project avoids hard-coded local paths. Prefer:

- Streamlit file uploaders for inputs
- `BytesIO` / in-memory buffers for generated files
- Streamlit download buttons for outputs
- Relative documentation paths such as `./samples`

Do not commit real secrets or API keys to GitHub.

## Decision-Support Disclaimer

TAIVAS is a decision-support simulation tool. It does not provide guaranteed
predictions, emergency commands, or final operational decisions. Results should
be reviewed together with real-time data, professional judgment, and
institutional protocols.
