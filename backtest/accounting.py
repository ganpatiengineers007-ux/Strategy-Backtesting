class EquityCurve:
    def __init__(self):
        self.points = []

    def record(self, ts, equity):
        self.points.append([ts, equity])
