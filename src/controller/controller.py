import docker
import time
import traceback

from threading import Thread

from modules.gateway import Gateway
from utils.utils import Utils
from utils.logger import info, warning, debug, error
from model.objects.atom import Atom
from model.objects.network import Network
from persistence.tinyops_db import db
from docker.errors import ImageNotFound


class Controller:

    def __init__(self, model):
        self._model = model
        self.docker_client = self._get_docker_client()
        self._containers = []
        self._sync_running = True
        self._sync_loop_thread = Thread(target=self._sync)
        self._gateway_manager = Gateway()

    def start(self):
        debug("Trying to start sync loop thread...")
        if self._sync_loop_thread and self._sync_loop_thread.is_alive():
            debug("Thread loop already running.")
            return

        self._sync_running = True
        self._sync_loop_thread = Thread(target=self._sync)
        self._sync_loop_thread.start()

    def stop(self):
        if self._sync_loop_thread and self._sync_loop_thread.is_alive():
            self._sync_running = False
            self._sync_loop_thread.join(timeout=2)
            if self._sync_loop_thread.is_alive():
                warning("Force stopping...")
        info("Sync loop thread stopped")
        return

    def _sync(self):
        debug("Syncing...")
        while self._sync_running:
            try:
                self._iterate()
            except BaseException:
                print(traceback.format_exc())
            time.sleep(2)

    def _iterate(self):
        self._model.sync()
        self._link_docker_containers_to_atoms()
        self._delete_unused_docker_containers()
        self._create_docker_networks_up_for_creation()
        self._delete_docker_containers_up_for_deletion()
        self._create_docker_containers_up_for_creation()
        self._recreate_illegally_removed_docker_containers()
        self._remove_unused_networks()
        self._remove_networks_up_for_deletion()
        self._create_ssl_certificates()
        self.update_gateway_configuration()

    def _get_docker_client(self):
        try:
            return docker.from_env()
        except Exception:
            raise Exception("Could not connect to Docker, make sure Docker is running and linked correctly.")

    def _get_docker_network_by_name(self, name):
        return next((n for n in self.docker_client.networks.list() if n.name == name), None)

    @property
    def _docker_containers(self):
        containers = []
        for container in self.docker_client.containers.list(all=True):
            if container.labels.get("tinyops_container_id"):
                containers.append(container)
        return containers

    @property
    def _docker_networks(self):
        networks = []
        for network in self.docker_client.networks.list():
            if network.attrs.get("Labels").get("tinyops_id"):
                networks.append(network)
        return networks

    def _is_docker_container_linked_to_atom(self, _id):
        return Atom.get_by_id(_id)

    def _link_docker_containers_to_atoms(self):
        for atom in self._model.atoms:
            if not atom.link:
                for docker_container in self._docker_containers:
                    if not self._is_docker_container_linked_to_atom(docker_container.labels["tinyops_container_id"]):
                        if atom.name == docker_container.labels["tinyops_name"]:
                            atom.link = docker_container
                            atom.id = docker_container.labels["tinyops_container_id"]
                            if not atom.image:
                                atom.image = docker_container.labels.get("tinyops_image", atom.image)
                            atom.up_for_creation = False
                            info(f"Linking {atom.name}")
                            break

    def _delete_unused_docker_containers(self):
        for docker_container in self._docker_containers:
            _id = docker_container.labels.get("tinyops_container_id")
            found = any(_id == atom.id for atom in self._model.atoms)
            if not found:
                info(f"Deleting {docker_container.name} - (unused)")
                docker_container.remove(force=True)

    def _delete_docker_containers_up_for_deletion(self):
        for atom in self._model.atoms[:]:
            if atom.up_for_deletion:
                if atom.link:
                    info(f"Deleting {atom.link.name} - (marked for deletion)")
                    atom.link.remove(force=True)
                    self._model.atoms.remove(atom)

    def _create_docker_containers_up_for_creation(self):
        for atom in self._model.atoms:
            if atom.ready_for_creation:
                info(f"Creating {atom.name}")
                
                ports_config = None
                if atom.ports:
                    ports_config = {}
                    for container_port, host_port in atom.ports.items():
                        ports_config[f"{container_port}/tcp"] = host_port
                
                volumes_config = {}
                for entry in atom.volumes:
                    host_path, container_path = entry.split(":")
                    volumes_config[host_path] = {'bind': container_path, 'mode': 'rw'}

                self._pull_image_if_it_doesnt_exist_locally(atom.image)

                docker_container = self.docker_client.containers.create(
                    image=atom.image,
                    name=f"{atom.name}-{Utils.generate_random_string(10)}",
                    detach=True,
                    labels={
                        "tinyops_container_id": atom.id,
                        "tinyops_name": atom.name,
                        "tinyops_image": atom.image
                    },
                    environment=atom.env,
                    ports=ports_config,
                    volumes=volumes_config
                )

                network = self.docker_client.networks.get("tinyops_network")
                network.connect(docker_container, aliases=[atom.name])

                atom.link = docker_container
                atom.up_for_creation = False

                self._start_container(docker_container)

    def _recreate_illegally_removed_docker_containers(self):
        for atom in self._model.atoms:
            try:
                if atom.link:
                    atom.link.reload()
                    if atom.link.status != "running":
                        self._start_container(atom.link)
            except docker.errors.NotFound:
                atom.up_for_creation = True

    def _start_container(self, container):
        try:
            container.start()
        except Exception as e:
            error(f"Failed to start Container {container.name} : {e}")

    def _pull_image_if_it_doesnt_exist_locally(self, image_name):
        try:
            self.docker_client.images.get(image_name)
        except ImageNotFound:
            info(f"Image: {image_name} not found, pulling...")
            self.docker_client.images.pull(image_name)
            info(f"Pulled Image: {image_name}")

    def _create_docker_networks_up_for_creation(self):
        for network in self._model.networks:
            if not self._get_docker_network_by_name(network.name):
                info(f"Creating Network {network.name}")
                self.docker_client.networks.create(
                    name=network.name,
                    labels={
                        "tinyops_id": network.id
                    }
                )

    def _remove_networks_up_for_deletion(self):
        for network in self._model.networks:
            if network.up_for_deletion:
                docker_network = self._get_docker_network_by_name(network.name)
                if docker_network:
                    self._remove_network(docker_network)
                self._model.networks.remove(network)

    def _remove_unused_networks(self):
        for network in self._docker_networks:
            if not Network.get_by_name(network.name):
                self._remove_network(network)

    def _remove_network(self, network):
        try:
            if network.name != "tinyops_network":
                info(f"Removing Network {network.name}")
                network.remove()
        except Exception as e:
            error(f"Error removing network: {network.name} - {str(e)}")

    def _create_ssl_certificates(self):
        self.update_gateway_configuration()
        domains = Atom.get_ssl_domains()
        for domain in domains:
            ssl_ready = db.get(domain, "ssl_ready")
            ssl_creation_failed = db.get(domain, "ssl_creation_failed")
            if not ssl_ready and not ssl_creation_failed:
                db.set(domain, "ssl_pending", True)
                self._gateway_manager.create_ssl_certificate(domain, Atom.get_gateway_atom().link)
                db.set(domain, "ssl_pending", False)

    def update_gateway_configuration(self):
        try:
            if self._gateway_manager.update_config():
                self._gateway_manager.load_config_to_the_gateway_container(Atom.get_gateway_atom().link)
                self._gateway_manager.reload_nginx(Atom.get_gateway_atom())
                info("Gateway config updated")
        except Exception as e:
            error(f"Gateway update error: {e}")


