from record import Record


class Reference:
    def __init__(self, key: str, id: str):
        self.key = key
        self.id = id

    def get_record(self) -> Record:
        pass
