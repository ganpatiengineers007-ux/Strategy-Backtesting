class EventQueue:
    """Market events ko time-order me deta hai: (index, bar)."""

    def __init__(self, bars):
        self.bars = bars

    def __iter__(self):
        return iter(enumerate(self.bars))
