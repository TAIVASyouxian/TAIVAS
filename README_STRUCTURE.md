# TAIVAS V6 Project Structure

TAIVAS V6 is a Streamlit-based resilience decision-support prototype with a cleaner SaaS-ready structure.

## Main entry file

```text
taivas_control_center_v6_saas_ready.py
```

This file remains the Streamlit UI controller. It handles page layout, controls, tab flow, and calls the separated model/export/render modules.

## Configuration files

```text
data_config.py
facility_config.py
i18n_config.py
```

These files store city/country scenario data, facility profiles, and interface language strings.

## Core package

```text
taivas_core/
├─ __init__.py
├─ utils.py
├─ energy_model.py
├─ trend_forecast.py
├─ export_center.py
└─ ui_render.py
```

### Module roles

- `utils.py`: shared helpers such as safe division, clamping, safe numeric parsing.
- `energy_model.py`: core energy supply, demand, renewable mix, battery, shortfall, and grid dependency calculations.
- `trend_forecast.py`: uploaded history sorting, rolling averages, recent trend estimates, forecast horizon logic, and confidence band preparation.
- `export_center.py`: CSV/TXT/JSON export payload preparation, executive summary, and audit-trail packaging.
- `ui_render.py`: reusable Streamlit rendering helpers and chart renderers.

## Existing project dependencies

The following existing files/folders should remain in your TAIVAS root folder:

```text
modules/
concept_lab_components.py
requirements.txt
```

Do not delete your older V1-V5 files until V6 is confirmed stable on Streamlit Cloud.
