from model.objects.atom import Atom
from model.objects.network import Network
from model.api_service import ApiService
from persistence.tinyops_db import db
from utils.logger import info, warning
from utils.utils import Utils


class Model:

    def __init__(self, parser):
        self._parser = parser
        self._blueprint = dict()
        self.api_service = ApiService(self)

    def sync(self):
        self._parser.load_blueprint()
        self._create_gateway()
        self._create_atoms()
        self._mark_unused_atoms_for_deletion()
        self._mark_unused_networks_for_deletion()
        self._delete_config_changed_atoms()
        self._update_config_changed_atoms()

    @property
    def atoms(self):
        return Atom.atoms

    @property
    def networks(self):
        return Network.networks

    def _create_gateway(self):
        self._parser.applications.insert(0, dict(
            name="TINYOPS_GATEWAY",
            image="tarik56/tinyops-gateway:0.0.1",
            network="tinyops_network",
            replicas=1,
            ports={
                "80": 80,
                "443": 443
            }
        ))

    def _create_atoms(self):
        for application in self._parser.applications:
            replicas = application.get("replicas", 1)
            name = application["name"]
            image = application.get("image")
            network = application.get("network")
            diff = replicas - len(self._get_active_atoms_by_name(name))
            env = application.get("env")
            ports = application.get("ports")
            domain = application.get("domain")
            ssl = application.get("ssl")
            volumes = application.get("volumes")
            git = application.get("git")

            if self._is_replica_more_than_ports(application):
                warning(f"Application {name} has more replicas than ports. Skipping creation.")
                continue

            if network:
                self._create_network_if_not_exists(network)

            if git:
                entry = self._add_git_repository_to_db(git)
                if entry:
                    git = entry

            if diff > 0:
                for _ in range(diff):
                    atom = Atom(
                        name=name,
                        image=image,
                        network=network,
                        env=env,
                        ports=ports,
                        volumes=volumes,
                        domain=domain,
                        ssl=ssl or False,
                        git=git
                    )
                    atom.up_for_creation = True
            if diff < 0:
                atoms = Atom.get_atoms_by_name(name)
                for x in range(abs(diff)):
                    atoms[x].up_for_deletion = True

    def _mark_unused_atoms_for_deletion(self):
        for atom in self.atoms:
            if atom.deletable:
                found = any(app["name"] == atom.name for app in self._parser.applications)
                if not found:
                    atom.up_for_deletion = True
        
    def _mark_unused_networks_for_deletion(self):
        for network in self.networks:
            found = any(app.get("network") == network.name for app in self._parser.applications)
            if not found:
                network.up_for_deletion = True

    def _is_replica_more_than_ports(self, application):
        ports = application.get("ports")
        replicas = application.get("replicas")
        if ports:
            return replicas > 1
        return False

    def _delete_config_changed_atoms(self):
        for application in self._parser.applications:
            for atom in self._get_active_atoms_by_name(application["name"]):
                if application.get("env"):
                    if str(atom.env) != str(application["env"]):
                        atom.up_for_deletion = True

                if application.get("image"):
                    if application["image"] != atom.image:
                        atom.up_for_deletion = True

                if application.get("network"):
                    if application["network"] != atom.network:
                        atom.up_for_deletion = True

                if application.get("ports"):
                    if str(atom.ports) != str(application["ports"]):
                        atom.up_for_deletion = True

                if application.get("volumes"):
                    if str(atom.volumes) != str(application.get("volumes")):
                        atom.up_for_deletion = True

                if application.get("git"):
                    app_git = application["git"]
                    if isinstance(app_git, dict):
                        app_git_url = app_git.get("url")
                        app_git_branch = app_git.get("branch")
                    else:
                        app_git_url = app_git
                        app_git_branch = None
                    if atom.git_url != app_git_url:
                        atom.up_for_deletion = True
                    if atom.git_branch != app_git_branch:
                        atom.up_for_deletion = True

                if atom.git and atom.link:
                    if db.get(atom.repo_name, "image_name") != atom.image:
                        atom.up_for_deletion = True

    def _update_config_changed_atoms(self):
        for application in self._parser.applications:
            for atom in self._get_active_atoms_by_name(application["name"]):
                domain = application.get("domain")
                if not domain:
                    atom.domain = None
                if domain:
                    if atom.domain != domain:
                        info(f"New Domain registration {domain} found for {atom.name}, updating it.")
                        atom.domain = domain

                ssl = application.get("ssl")
                if ssl is not None:
                    if atom.ssl != ssl:
                        info(f"SSL updated for {atom.name}, set to {ssl}")
                        atom.ssl = ssl

    def _create_network_if_not_exists(self, name):
        if not Network.get_by_name(name):
            network = Network(name)
            network.up_for_creation = True

    def _add_git_repository_to_db(self, git):
        git_url = git.get("url")
        git_branch = git.get("branch")
        if git_url and git_branch:
            repo_name = Utils.extract_repo_name_from_git_url_and_branch(git_url, git_branch)
            entry = dict(
                url=git_url, 
                branch=git_branch, 
                repo_name=repo_name
            )
            db.append_to_list_if_not_exists("repos", entry)
            return entry
        return None


    def _get_active_atoms_by_name(self, name):
        atoms = []
        for atom in self.atoms:
            if atom.name == name and not atom.up_for_deletion:
                atoms.append(atom)
        return atoms
