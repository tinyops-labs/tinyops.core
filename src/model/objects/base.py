from utils.utils import Utils


class Base:

    def __init__(self, name):
        self.id = Utils.generate_random_string()
        self.name = name
        self.up_for_creation = False
        self.up_for_deletion = False
        self.deletable = True

    def __dict__(self):
        return dict(
            id=self.id,
            name=self.name,
            up_for_creation=self.up_for_creation,
            up_for_deletion=self.up_for_deletion,
            deletable=self.deletable
        )
