# TAIVAS V9.2 Demo Auto-Fill

V9.2 integrates the V9.1 onboarding layer with true demo auto-fill behavior.

## Main file path

```text
taivas_control_center_v9_2_demo_autofill.py
```

## What changed

- Added guided demo buttons in the onboarding panel.
- Added sidebar Demo Mode options:
  - Taipei Typhoon Test
  - Helsinki Blizzard Test
  - Berlin Heatwave Test
  - Reykjavik Storm Test
- Pressing a guided demo button stores the selected preset in Streamlit session state and reruns the app.
- The selected demo preset then auto-fills the runtime scenario values:
  - country
  - city
  - population
  - weather scenario
  - temperature
  - wind speed
  - solar radiation
  - precipitation
  - humidity
  - selected failure ratios
  - energy security scenario where applicable

## Notes

This version does not change the core model formulas. It is an onboarding/product usability improvement.
