import time
import os
from unittest import TestCase

from parser.parser import Parser
from model.model import Model
from model.objects.atom import Atom
from model.objects.network import Network
from controller.controller import Controller
from utils.utils import Utils


class TestTinyOps(TestCase):

    # remove all db files
    for file in os.listdir("."):
        if file.endswith(".db"):
            os.remove(file)

    parser = Parser(test=True)
    model = Model(parser=parser)
    controller = Controller(model=model)

    def setBlueprint(self, data, iterate=True):
        TestTinyOps.parser._blueprint = data
        if iterate:
            TestTinyOps.controller._iterate()

    def setUp(self):
        TestTinyOps.controller.stop()
        self.removeAllTinyOpsContainers()
        self.waitForContainerCountToReach(0)

    def tearDown(self):
        Atom.atoms = []
        Network.networks = []
        TestTinyOps.parser._blueprint = dict()
        self.removeAllTinyOpsContainers()
        self.waitForContainerCountToReach(0)
        self.removeAllTinyOpsNetworks()


    def removeAllTinyOpsContainers(self):
        for container in TestTinyOps.controller._docker_containers:
            container.remove(force=True)
    
    def removeAllTinyOpsNetworks(self):
        for network in TestTinyOps.controller._docker_networks:
            network.remove()

    def waitForAtomLink(self, atom):
        total_wait = 0
        while not atom.link:
            time.sleep(0.1)
            total_wait += 0.1
            if total_wait > 10:
                raise Exception("Timeout: Could not establish Link by atom creation")
        return atom.link

    def waitForContainerCountToReach(self, count):
        total_wait = 0
        while len(TestTinyOps.controller._docker_containers) != count:
            time.sleep(0.1)
            total_wait += 0.1
            if total_wait > 10:
                raise Exception("Timeout: Could not reach container count")
        return True

    def waitForGateWayConfigToBeTransferred(self):
        total_wait = 0
        while not Atom.get_gateway_atom().link:
            time.sleep(0.1)
            total_wait += 0.1
            if total_wait > 10:
                raise Exception("Timeout: Could not transfer gateway config")
        return True

    def test_container_creation_modification_and_deletion(self):
        network = Utils.generate_random_string(16)
        name = Utils.generate_random_string(8)
        self.setBlueprint(dict(
            applications=[
                dict(
                    name=name,
                    replicas=1,
                    image="nginx:latest",
                    network=network,
                    env=dict(
                        username="admin",
                        password="pass"
                    ),
                    ports=dict(
                        **{"80": 8080}
                    )
                )
            ]
        ))
        self.waitForContainerCountToReach(2)
        print(f"name= {Atom.get_atoms_by_name(name)[0].name}")
        atom = Atom.get_atoms_by_name(name)[0]
        assert atom.name == name
        assert atom.ports == {"80": 8080}
        link = self.waitForAtomLink(atom)
        assert link.attrs['Config']['Env'][0] == "username=admin"
        assert link.attrs['Config']['Env'][1] == "password=pass"

        self.setBlueprint(dict(
            applications=[
                dict(
                    name=name,
                    replicas=1,
                    image="nginx:latest",
                    network=network,
                    env=dict(
                        username="admin2",
                        password="pass2"
                    ),
                    ports=dict(
                        **{"80": 8080}
                    )
                )
            ]
        ))
        TestTinyOps.controller._iterate()
        assert self.waitForContainerCountToReach(2)
        atom = Atom.get_atoms_by_name(name)[0]
        assert atom.env == {"username": "admin2", "password": "pass2"}
        link = self.waitForAtomLink(atom)
        assert link.attrs['Config']['Env'][0] == "username=admin2"
        assert link.attrs['Config']['Env'][1] == "password=pass2"
        assert self.waitForContainerCountToReach(2)

        self.setBlueprint(dict(
            applications=[
                dict(
                    name=name,
                    replicas=0,
                    image="nginx:latest",
                    network=network,
                    env=dict(
                        username="admin",
                        password="pass"
                    ),
                    ports=dict(
                        **{"80": 8080}
                    )
                )
            ]
        ))
        assert self.waitForContainerCountToReach(1)
        atom = Atom.get_atoms_by_name(name)
        assert len(atom) == 0

    def test_container_replication(self):
        network = Utils.generate_random_string(16)
        name = Utils.generate_random_string(8)
        self.setBlueprint(dict(
            applications=[
                dict(
                    name=name,
                    replicas=3,
                    image="nginx:latest",
                    network=network,
                    env=dict(
                        username="admin",
                        password="pass"
                    )
                )
            ]
        ))
        assert self.waitForContainerCountToReach(4)
        atoms = Atom.get_atoms_by_name(name)
        assert len(atoms) == 3
        for atom in atoms:
            assert atom.env == {"username": "admin", "password": "pass"}
            link = self.waitForAtomLink(atom)
            assert link.attrs['Config']['Env'][0] == "username=admin"
            assert link.attrs['Config']['Env'][1] == "password=pass"