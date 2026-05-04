"""TAIVAS utility helpers V10.2."""

from __future__ import annotations


def clamp(value, low, high):
    try:
        value = float(value)
    except Exception:
        value = low
    return max(low, min(high, value))


def safe_div(numerator, denominator, default=0.0):
    try:
        denominator = float(denominator)
        if denominator == 0:
            return default
        return float(numerator) / denominator
    except Exception:
        return default
