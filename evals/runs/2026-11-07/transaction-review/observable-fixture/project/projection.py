"""Local event/projection simulation; no Qt, UE or GUI runtime."""
TRACE_ENABLED = False
TRACE = []

def trace(event):
    if TRACE_ENABLED:
        TRACE.append(event)

class Owner:
    def __init__(self):
        self.count = 0
        self.listeners = []
    def set_count(self, value):
        self.count = value
        trace(('owner_changed', value))
        for listener in list(self.listeners):
            listener(value)

class Panel:
    def __init__(self):
        self.displayed = 0
        self.owner = None
    def refresh(self, value):
        trace(('refresh', value))
        self.displayed = value
    def mount(self, owner):
        self.owner = owner
        owner.listeners.append(self.refresh)
        self.refresh(owner.count)

def reproduce():
    TRACE.clear()
    owner = Owner()
    panel = Panel()
    owner.set_count(7)
    panel.mount(owner)
    return {'owner': owner.count, 'displayed': panel.displayed, 'trace': list(TRACE)}

if __name__ == '__main__':
    print(reproduce())
