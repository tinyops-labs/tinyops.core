import pickle
import shelve


class TinyOpsDB:

    def __init__(self):
        self.db = shelve.open("tinyops.db", "c")

    def get(self, first, second=None):
        key = first if second is None else f"{first}_{second}"
        try:
            return self.db.get(key)
        except pickle.UnpicklingError:
            try:
                del self.db[key]
            except KeyError:
                pass
            self.db.sync()
            return None

    def set(self, first, second=None, value=None):
        if second is None:
            self.db[first] = value
        else:
            self.db[f"{first}_{second}"] = value
        self.db.sync()

    def get_list(self, first):
        list_ = self.get(first)
        if list_ is None:
            self.set(first, value=[])
            list_ = self.get(first)
        return list_

    def append_to_list(self, first, value):
        list_ = self.get_list(first)
        list_.append(value)
        self.set(first, value=list_)

    def append_to_list_if_not_exists(self, first, value):
        list_ = self.get_list(first)
        if value not in list_:
            list_.append(value)
        self.set(first, value=list_)

    def remove_from_list(self, first, value):
        list_ = self.get_list(first)
        list_.remove(value)
        self.set(first, value=list_)

    def dump_db(self):
        return self.db

    def internal_snapshot(self):
        return {str(k): self.db[k] for k in list(self.db.keys())}


db = TinyOpsDB()
