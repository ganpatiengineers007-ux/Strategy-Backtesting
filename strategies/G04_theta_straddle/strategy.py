"""G04 Theta short-straddle  (plug-in adapter, Greeks strategy G04)

अभी सिर्फ़ ढाँचा। यह strategy दो options बेचती है (short straddle), जबकि registry का
Signal v0 सिर्फ़ long-only (BUY/EXIT) है और options legs नहीं जानता।
पूरा backtest: all_strategies/greeks/theta_straddle_strategy.py (अलग से चलता है)।
Signal v1 (short + options legs) आने पर यहाँ on_bar भरा जाएगा।
"""
from strategies.base import Strategy


class ThetaStraddleAdapter(Strategy):
    strategy_id = "theta_straddle"
    required_data = ()

    def on_bar(self, ctx):
        return None   # जानबूझकर खाली: ऊपर वजह लिखी है
