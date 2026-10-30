import pandas as pd
from .indicators import book_imbalance, oi_change_pct

def microstructure_allows(frame: pd.DataFrame, i: int, side: str,
                          require_orderbook: bool, min_book_imbalance: float,
                          require_oi: bool, min_oi_change_pct: float) -> tuple[bool, str]:
    # A long needs positive bid-side imbalance; a short needs negative imbalance.
    imbalance = book_imbalance(frame).iloc[i]
    if require_orderbook:
        if pd.isna(imbalance):
            return False, "ORDERBOOK_MISSING"
        if side == "BUY" and imbalance < min_book_imbalance:
            return False, "BID_DEPTH_NOT_CONFIRMED"
        if side == "SELL" and imbalance > -min_book_imbalance:
            return False, "ASK_DEPTH_NOT_CONFIRMED"

    # OI change is treated as a participation/positioning confirmation, not direction
    # by itself. Positive OI expansion is required when require_oi=True.
    oi_pct = oi_change_pct(frame).iloc[i]
    if require_oi:
        if pd.isna(oi_pct):
            return False, "OI_MISSING_OR_ZERO_BASE"
        if oi_pct < min_oi_change_pct:
            return False, "OI_EXPANSION_NOT_CONFIRMED"
    return True, "MICROSTRUCTURE_OK"
