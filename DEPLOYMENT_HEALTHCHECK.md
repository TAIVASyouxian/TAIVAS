# TAIVAS V7 Deployment Health Check

After deployment, verify these items:

1. App opens successfully.
2. Country and city selectors work.
3. Weather scenario selector changes results.
4. Energy Mix tab loads charts.
5. Scenario Comparison tab loads without error.
6. Trend / Forecast section loads.
7. Download buttons produce files.
8. Concept Lab still opens.
9. No `ModuleNotFoundError` appears in logs.
10. Main file path points to `taivas_control_center_v7_docker_ready.py`.

If deployment fails, check:

- `requirements.txt` exists at repo root.
- `taivas_core/` exists at repo root.
- `modules/` exists at repo root.
- `concept_lab_components.py` exists at repo root.
- Main file path matches the V7 file name exactly.
