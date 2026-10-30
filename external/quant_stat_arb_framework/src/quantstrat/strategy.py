import logging
import pandas as pd
from .config import StrategyConfig
from .indicators import validate_ohlcv, rolling_zscore, atr
from .microstructure import microstructure_allows
from .models import Signal, Side

log = logging.getLogger(__name__)

class MeanReversionStrategy:
    def __init__(self, config: StrategyConfig):
        self.config = config

    def prepare(self, data: pd.DataFrame) -> pd.DataFrame:
        validate_ohlcv(data)
        out = data.copy()
        out["z_score"] = rolling_zscore(out["close"], self.config.lookback)
        out["volume_ma"] = out["volume"].rolling(
            self.config.volume_lookback,
            min_periods=self.config.volume_lookback
        ).mean()
        out["atr"] = atr(out, self.config.atr_period)
        return out

    def generate_signals(self, data: pd.DataFrame) -> list[Signal]:
        frame = self.prepare(data)
        cfg = self.config
        signals = []
        for i in range(1, len(frame)):
            row, prev = frame.iloc[i], frame.iloc[i - 1]
            if pd.isna(row["z_score"]) or pd.isna(prev["z_score"]) or pd.isna(row["atr"]):
                continue
            if pd.isna(row["volume_ma"]) or row["volume"] <= row["volume_ma"] * cfg.volume_multiplier:
                continue

            # Cross-back: fade only after the extreme starts reverting.
            # Touch mode is more aggressive and enters while the threshold is breached.
            long_trigger = (
                row["z_score"] <= -cfg.z_entry if cfg.entry_mode == "touch"
                else prev["z_score"] <= -cfg.z_entry and row["z_score"] > prev["z_score"]
            )
            short_trigger = (
                row["z_score"] >= cfg.z_entry if cfg.entry_mode == "touch"
                else prev["z_score"] >= cfg.z_entry and row["z_score"] < prev["z_score"]
            )

            if cfg.allow_long and long_trigger:
                allowed, reason = microstructure_allows(
                    frame, i, "BUY", cfg.require_orderbook, cfg.min_book_imbalance,
                    cfg.require_oi, cfg.min_oi_change_pct
                )
                if allowed:
                    signals.append(Signal(frame.index[i], Side.BUY, float(row["z_score"]),
                                          float(row["close"]), float(row["atr"]),
                                          "Z_REVERSION_LONG|VOLUME_OK|" + reason))
            elif cfg.allow_short and short_trigger:
                allowed, reason = microstructure_allows(
                    frame, i, "SELL", cfg.require_orderbook, cfg.min_book_imbalance,
                    cfg.require_oi, cfg.min_oi_change_pct
                )
                if allowed:
                    signals.append(Signal(frame.index[i], Side.SELL, float(row["z_score"]),
                                          float(row["close"]), float(row["atr"]),
                                          "Z_REVERSION_SHORT|VOLUME_OK|" + reason))
        return signals
