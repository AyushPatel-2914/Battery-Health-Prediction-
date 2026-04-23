"""Data transformation helpers used by Test visualizations."""

import numpy as np


def build_time_series(df):
    """Convert tower simulation output into time-series matrices.

    The returned matrices are indexed by datetime and contain
    tower-level effective users and battery state of charge.
    """
    df_sorted = df.sort_values("datetime")
    load_pivot = df_sorted.pivot(
        index="datetime",
        columns="tower_id",
        values="effective_users"
    ).fillna(0)
    battery_pivot = df_sorted.pivot(
        index="datetime",
        columns="tower_id",
        values="battery_soc_percent"
    ).fillna(0)
    return load_pivot, battery_pivot
