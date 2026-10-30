class SimClock:
    def __init__(self):
        self.now = None

    def set(self, ts):
        self.now = ts
