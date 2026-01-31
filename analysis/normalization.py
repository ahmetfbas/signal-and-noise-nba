# analysis/normalization.py

from __future__ import annotations

def clip(x: float, lo: float, hi: float) -> float:
    if x is None:
        return None
    return max(lo, min(hi, float(x)))

def clip01(x: float) -> float:
    return clip(x, 0.0, 1.0)

def minmax_01(x: float, lo: float, hi: float) -> float:
    if x is None:
        return None
    if hi == lo:
        return 0.5
    return clip01((float(x) - lo) / (hi - lo))

def z_to_01(z: float, z_lo: float = -2.0, z_hi: float = 2.0) -> float:
    # map z-score into [0,1] by clipping a reasonable z-range
    return minmax_01(z, z_lo, z_hi)

def to_minus1_plus1(x01: float) -> float:
    # map [0,1] -> [-1,1]
    if x01 is None:
        return None
    return clip(float(x01) * 2.0 - 1.0, -1.0, 1.0)

def normalize_momentum(delta: float) -> float:
    """
    Convert rpm delta values (usually between -10 and +10)
    into a -1..1 bounded momentum score.
    """
    if delta is None:
        return 0.0
    # assume normal spread −10 → +10
    return to_minus1_plus1(clip01((delta + 10.0) / 20.0))
