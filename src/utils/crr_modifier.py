"""
Statistical calculations for simulation results.
"""

import numpy as np
from scipy import stats
from typing import Tuple


def calculate_confidence_interval(data, confidence: float = 0.95) -> Tuple[float, float, float, int]:
    """
    Calculate confidence interval for a dataset.
    
    Args:
        data: Array-like data
        confidence: Confidence level (default 0.95)
    
    Returns:
        Tuple of (mean, ci_lower, ci_upper, n)
    """
    arr = np.array(data, dtype=float)
    
    if len(arr) < 2 or np.all(np.isnan(arr)):
        return np.nan, np.nan, np.nan, len(arr)
    
    mean = np.nanmean(arr)
    std = np.nanstd(arr, ddof=1)
    n = int(np.sum(~np.isnan(arr)))
    
    if n < 2:
        return mean, np.nan, np.nan, n
    
    sem = std / np.sqrt(n)
    t_crit = stats.t.ppf((1 + confidence) / 2, df=n - 1)
    
    return mean, mean - t_crit * sem, mean + t_crit * sem, n
