"""ExecutionModel: slippage + fees + fill rules ek jagah (engine seedha slippage/fees nahi bulata)."""
from backtest import fees, slippage, stop_manager


class ExecutionModel:
    def __init__(self, slippage_bps=2.0, fee_pct=0.0003, ambiguous_candle_policy="stop_first"):
        if slippage_bps < 0 or fee_pct < 0:
            raise ValueError("slippage_bps aur fee_pct negative nahi ho sakte")
        self.slippage_bps, self.fee_pct, self.policy = slippage_bps, fee_pct, ambiguous_candle_policy

    def fill_entry(self, ref_price, qty):
        px = slippage.apply(ref_price, "BUY", self.slippage_bps)
        return px, fees.fee(qty * px, self.fee_pct)

    def fill_exit(self, raw_price, qty):
        px = slippage.apply(raw_price, "SELL", self.slippage_bps)
        return px, fees.fee(qty * px, self.fee_pct)

    def check_exit(self, position, bar):
        return stop_manager.check(position, bar, self.policy)
