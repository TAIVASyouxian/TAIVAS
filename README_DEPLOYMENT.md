# TAIVAS V6 Deployment Guide

## Streamlit Cloud

1. Upload all V6 files to the root of your GitHub repository.
2. Confirm the repository root includes:

```text
taivas_control_center_v6_saas_ready.py
data_config.py
facility_config.py
i18n_config.py
taivas_core/
modules/
concept_lab_components.py
requirements.txt
```

3. In Streamlit Cloud, create a new app or edit the test app.
4. Set the main file path to:

```text
taivas_control_center_v6_saas_ready.py
```

5. Deploy or reboot.

## Recommended testing checklist

After deployment, test these functions:

- Country/city switching
- Facility type switching
- Weather scenario switching
- Energy Mix tab
- Scenario Comparison tab
- Stress Test tab
- AI Recommendation tab
- Energy Security tab
- Survival Timeline tab
- Visual Simulator tab
- Concept Lab tab
- CSV download
- TXT executive summary download
- JSON audit trail download
- Uploaded history preview and forecast chart

## Rollback plan

Keep the V5 app online while testing V6.

If V6 fails, switch the Streamlit Cloud main file path back to:

```text
taivas_control_center_v5_ui_split.py
```

or use the existing V5 deployed app.
