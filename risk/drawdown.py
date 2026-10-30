class DrawdownTracker:
    def __init__(self):
        self.peak = None

    def update(self, equity):
        self.peak = equity if self.peak is None else max(self.peak, equity)
        return 0.0 if not self.peak else (self.peak - equity) / self.peak * 100.0
