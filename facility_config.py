# Auto-generated from taivas_control_center(13).py
# V1 safe config split: facility config only.

FACILITY_PROFILES = {
    "Long-term Care": {
        "critical_load_share": 0.48,
        "temp_band_c": "20–26",
        "notes": "Temperature stability, life-support continuity, and water systems are highly sensitive.",
        "priority_order": ["Medical", "Heating/Cooling", "Water Systems", "Communications"],
        "critical_split": {"Medical": 0.34, "Heating/Cooling": 0.28, "Water Systems": 0.22, "Communications": 0.16},
        "failure_tolerance_hours": 6,
    },
    "Hospital": {
        "critical_load_share": 0.58,
        "temp_band_c": "19–24",
        "notes": "ICU, surgery, pharmacy refrigeration, and core communications require stronger protection.",
        "priority_order": ["Medical", "Water Systems", "Heating/Cooling", "Communications"],
        "critical_split": {"Medical": 0.42, "Heating/Cooling": 0.22, "Water Systems": 0.18, "Communications": 0.18},
        "failure_tolerance_hours": 4,
    },
    "Data Center": {
        "critical_load_share": 0.52,
        "temp_band_c": "18–27",
        "notes": "Thermal stability and core digital continuity dominate the resilience profile.",
        "priority_order": ["Heating/Cooling", "Communications", "Water Systems", "Medical"],
        "critical_split": {"Medical": 0.05, "Heating/Cooling": 0.46, "Water Systems": 0.14, "Communications": 0.35},
        "failure_tolerance_hours": 3,
    },
    "School / Campus": {
        "critical_load_share": 0.28,
        "temp_band_c": "18–29",
        "notes": "Lower life-support sensitivity, but sheltering, water, and communications still matter.",
        "priority_order": ["Heating/Cooling", "Water Systems", "Communications", "Medical"],
        "critical_split": {"Medical": 0.08, "Heating/Cooling": 0.38, "Water Systems": 0.28, "Communications": 0.26},
        "failure_tolerance_hours": 12,
    },
    "Residential Block": {
        "critical_load_share": 0.22,
        "temp_band_c": "16–30",
        "notes": "Basic habitability, water, and communications matter more than clinical continuity.",
        "priority_order": ["Heating/Cooling", "Water Systems", "Communications", "Medical"],
        "critical_split": {"Medical": 0.07, "Heating/Cooling": 0.44, "Water Systems": 0.29, "Communications": 0.20},
        "failure_tolerance_hours": 16,
    },
}

