"""Utilities for creating and mutating configuration dictionaries."""

import numpy as np


def build_noisy_config(base_config,
                       battery_noise=0.05,
                       coverage_noise=0.03,
                       power_noise=0.05):
    """Return a copy of the base config with added random noise.

    This helper keeps the original simulation parameters intact while
    producing a noisy variant used for Test scenario variability.
    """
    noisy_config = base_config.copy()
    noisy_config["battery_capacity_Wh"] = (
        base_config["battery_capacity_Wh"]
        * (1 + np.random.normal(0, battery_noise))
    )
    noisy_config["idle_power"] = (
        base_config["idle_power"]
        * (1 + np.random.normal(0, battery_noise))
    )
    noisy_config["base_coverage_radius"] = (
        base_config["base_coverage_radius"]
        * (1 + np.random.normal(0, coverage_noise))
    )
    noisy_config["base_tx_power"] = (
        base_config["base_tx_power"]
        * (1 + np.random.normal(0, power_noise))
    )
    return noisy_config
