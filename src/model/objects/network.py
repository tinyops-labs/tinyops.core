from model.objects.base import Base


class Network(Base):

    networks = []

    def __init__(self, name):
        super().__init__(name)
        Network.networks.append(self)

    @staticmethod
    def get_by_name(name_):
        for network in Network.networks:
            if network.name == name_:
                return network
        return None

    @staticmethod
    def get_by_id(id_):
        for network in Network.networks:
            if network.id == id_:
                return network
        return None
