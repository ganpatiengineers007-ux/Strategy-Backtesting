"""Fair Value Gap / institutional imbalance mapping: displacement candle leaves a 3-bar gap; wait for the
return into the zone and a rejecting close; stop beyond the gap, fixed R-multiple target."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .base import Strategy
from ..utils import rmean, shift


@dataclass
class FVGConfig:
    min_gap_bps: float = 1.5
    disp_mult: float = 2.0
    vol_win: int = 50
    max_age: int = 60
    rr: float = 2.0
    max_hold: int = 40
    stop_buf: float = 0.1       # fraction of gap size


class FVGStrategy(Strategy):
    name = "S08 Fair Value Gap / Imbalance"

    def __init__(self, cfg: FVGConfig | None = None):
        self.cfg = cfg or FVGConfig()

    def positions(self, bars) -> np.ndarray:
        c = self.cfg
        o, h, l, cl = bars.open, bars.high, bars.low, bars.close
        rng = h - l
        avg = shift(rmean(rng, c.vol_win), 1, np.nan)
        pos = np.zeros(bars.n)
        gaps = []
        cur, held, stop, tgt = 0, 0, 0.0, 0.0
        for i in range(2, bars.n):
            if cur:
                held += 1
                if (cur == 1 and (cl[i] <= stop or cl[i] >= tgt)) or (cur == -1 and (cl[i] >= stop or cl[i] <= tgt)) or held >= c.max_hold:
                    cur = 0
            if not np.isnan(avg[i - 1]) and rng[i - 1] >= c.disp_mult * avg[i - 1]:
                if l[i] > h[i - 2] and (l[i] - h[i - 2]) / cl[i] * 1e4 >= c.min_gap_bps:
                    gaps.append({"d": 1, "lo": h[i - 2], "hi": l[i], "born": i})
                elif h[i] < l[i - 2] and (l[i - 2] - h[i]) / cl[i] * 1e4 >= c.min_gap_bps:
                    gaps.append({"d": -1, "lo": h[i], "hi": l[i - 2], "born": i})
            keep = []
            for g in gaps:
                alive = (i - g["born"] <= c.max_age) and not (g["d"] == 1 and cl[i] < g["lo"]) and not (g["d"] == -1 and cl[i] > g["hi"])
                if not alive:
                    continue
                if cur == 0 and g["born"] < i:
                    size, mid_ = g["hi"] - g["lo"], 0.5 * (g["hi"] + g["lo"])
                    if g["d"] == 1 and l[i] <= g["hi"] and cl[i] > mid_ and cl[i] > o[i]:
                        cur, held, stop = 1, 0, g["lo"] - c.stop_buf * size
                        tgt = cl[i] + c.rr * (cl[i] - stop)
                        continue
                    if g["d"] == -1 and h[i] >= g["lo"] and cl[i] < mid_ and cl[i] < o[i]:
                        cur, held, stop = -1, 0, g["hi"] + c.stop_buf * size
                        tgt = cl[i] - c.rr * (stop - cl[i])
                        continue
                keep.append(g)
            gaps = keep
            pos[i] = cur
        return pos
