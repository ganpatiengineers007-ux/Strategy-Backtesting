class KillSwitch:
    def __init__(self):
        self.tripped, self.reason = False, ""

    def trip(self, reason):
        if not self.tripped:
            self.tripped, self.reason = True, reason
