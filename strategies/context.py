"""Context: strategy sirf current bar aur pichhli bars dekh sakti hai (prev)."""


class Context:
    def __init__(self, bars, index, position):
        self._bars, self.index, self.position = bars, index, position

    @property
    def bar(self):
        return self._bars[self.index]

    def prev(self, n=1):
        j = self.index - n
        return self._bars[j] if j >= 0 else None
