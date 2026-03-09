"""
Statistical calculations for simulation results.

Provides confidence interval computation for fuel consumption data
collected across multiple Monte Carlo trials.
"""

import numpy as np
from scipy import stats
from typing import Tuple


def calculate_confidence_interval(
    data, confidence: float = 0.95
) -> Tuple[float, float, float, int, float]:
    """
    Calculate confidence interval for a dataset using t-distribution.

    Args:
        data:       Array-like of fuel consumption values
        confidence: Confidence level (default 0.95 for 95% CI)

    Returns:
        Tuple of (mean, ci_lower, ci_upper, n, sem)
    """
    arr = np.array(data, dtype=float)

    if len(arr) < 2 or np.all(np.isnan(arr)):
        return np.nan, np.nan, np.nan, len(arr), np.nan

    mean = np.nanmean(arr)
    std = np.nanstd(arr, ddof=1)
    n = int(np.sum(~np.isnan(arr)))

    if n < 2:
        return mean, np.nan, np.nan, n, np.nan

    sem = std / np.sqrt(n)
    t_crit = stats.t.ppf((1 + confidence) / 2, df=n - 1)

    return mean, mean - t_crit * sem, mean + t_crit * sem, n, sem
