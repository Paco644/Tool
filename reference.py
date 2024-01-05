from misc import System


class Reference:
    def __init__(self, system: System, entity: str, id: str):
        from record import get_record

        self.system = system
        self.entity = entity
        self.id = id
        self.record = get_record(self.system, self.entity, id)
