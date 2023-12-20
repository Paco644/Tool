from misc import System, to_plural, Extension


class Reference:
    def __init__(self, system: System, key: str, id: str):
        from record import get_record

        self.system = system
        self.entity = Extension[key].value
        self.key = key
        self.id = id
        self.record = get_record(self.system, self.entity, id)
