# TAIVAS Deployment Portability Notes

TAIVAS currently remains a Streamlit app with the stable entry point:

```bash
streamlit run taivas_control_center.py
```

## Current Stable Mode

- Streamlit Cloud compatible.
- No database is required.
- Audit trails remain exportable JSON from the UI.
- Core formulas, scenario logic, and chart data sources remain inside the existing app workflow.
- The official entry point delegates deterministic energy-balance calculations
  to `core/energy_balance_phase2.py`; Streamlit remains the presentation layer.

## Optional Environment Variables

These variables are optional. If they are not set, the app uses Streamlit Cloud-safe defaults.

| Variable | Default | Purpose |
| --- | --- | --- |
| `TAIVAS_ENV` | `local` | Runtime label for audit metadata and deployment diagnostics. |
| `TAIVAS_PAGE_TITLE` | `TAIVAS Scenario-Based Energy Resilience Simulator` | Browser/app title. |
| `TAIVAS_LAYOUT` | `wide` | Streamlit page layout. |
| `TAIVAS_AUDIT_BACKEND` | `export_only` | Future audit backend selector. Current stable mode is export-only. |
| `TAIVAS_AUDIT_LOG_PATH` | empty | Reserved for future local JSONL logging when explicitly enabled. |

## Platform Migration Readiness

The app can later be deployed to platforms such as Render, Railway, Azure App Service, AWS, or GCP by keeping the same command:

```bash
streamlit run taivas_control_center.py --server.port $PORT --server.address 0.0.0.0
```

Use the platform's environment-variable panel to configure optional values.

## Future Persistence Interface

The current governance layer exposes an audit metadata interface but does not write server-side logs by default. This is intentional for Streamlit Cloud stability.

Future versions can route audit records to:

- managed PostgreSQL
- object storage
- cloud logging
- local JSONL files on platforms with persistent disks

Do not enable persistent logging on ephemeral filesystems unless the deployment platform guarantees storage durability.

## Dependency Policy

`requirements.txt` is intentionally minimal:

- `streamlit`
- `pandas`
- `matplotlib`
- `openpyxl`
- `xlrd`
- `pillow`
- `reportlab`
- `python-pptx`

Avoid adding heavy dependencies unless they are required for a specific migration target.
