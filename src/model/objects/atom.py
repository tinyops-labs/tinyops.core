
from model.objects.base import Base
from persistence.tinyops_db import db


class Atom(Base):

    atoms = []

    def __init__(self, name, image, network=None, env=None, ports=None, volumes=None, domain=None, ssl=False, git=None):
        super().__init__(name)
        self.env = env or dict()
        self.ports = ports or dict()
        self.volumes = volumes or dict()
        self.link = None
        self.image = image
        self.network = network
        self.domain = domain
        self.ssl = ssl
        self.git = git
        self.stats = None
        #threading.Thread(target=self.update_stats).start()
        Atom.atoms.append(self)

    @property
    def git_url(self):
        if isinstance(self.git, dict):
            return self.git.get("url")
        return None

    @property
    def git_branch(self):
        if isinstance(self.git, dict):
            return self.git.get("branch")
        return None

    @property
    def repo_name(self):
        if isinstance(self.git, dict):
            return self.git.get("repo_name")
        return None

    @property
    def ready_for_creation(self):
        if self.up_for_creation:
            if self.repo_name:
                if db.get(self.repo_name, "image_name"):
                    self.image = db.get(self.repo_name, "image_name")
                    return True
                return False
            return True
        return False

    @property
    def created_at(self):
        if self.link:
            return self.link.attrs['Created']
        return None

    def update_stats(self):
        while True:
            if self.link:
                self.stats = self.link.stats(stream=False)

    def get_container_logs(self):
        if self.link:
            return self.link.logs(tail=100).decode("utf-8").splitlines()
        return ""

    def get_cpu_percentage(self):
        if self.stats:
            cpu_delta = self.stats["cpu_stats"]["cpu_usage"]["total_usage"] - self.stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = self.stats["cpu_stats"]["system_cpu_usage"] - self.stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(self.stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100.0
            return round(cpu_percent, 2)
        return 0

    def get_memory_usage_in_mb(self):
        if self.stats:
            mem_usage = self.stats["memory_stats"]["usage"]
            mem_usage_mb = mem_usage / (1024 * 1024)

            return round(mem_usage_mb, 2)
        return 0

    @staticmethod
    def get_by_id(id_):
        for atom in Atom.atoms:
            if atom.id == id_:
                return atom
        return None

    @staticmethod
    def get_atoms_by_name(name):
        return [atom for atom in Atom.atoms if atom.name == name]

    @staticmethod
    def get_gateway_atom():
        for atom in Atom.atoms:
            if atom.name == "TINYOPS_GATEWAY":
                return atom
        return None

    @staticmethod
    def get_ssl_domains():
        domains = []
        for atom in Atom.atoms:
            if atom.domain and atom.ssl and atom.domain not in domains:
                domains.append(atom.domain)
        return domains

    @staticmethod
    def get_domains():
        domains = []
        for atom in Atom.atoms:
            if atom.domain and atom.domain not in [domain["domain"] for domain in domains]:
                domains.append(dict(name=atom.name, domain=atom.domain, ssl=atom.ssl))
        return domains

    @staticmethod
    def get_git_urls():
        urls = []
        for atom in Atom.atoms:
            if atom.git_url and atom.git_url not in urls:
                urls.append(atom.git_url)
        return urls

    def __dict__(self):
        return dict(
            id=self.id,
            name=self.name,
            up_for_creation=self.up_for_creation,
            up_for_deletion=self.up_for_deletion,
            deletable=self.deletable,
            image=self.image,
            network=self.network,
            domain=self.domain,
            ssl=self.ssl,
            env=self.env,
            ports=self.ports,
            volumes=self.volumes,
            link=True if self.link else False,
            created_at=self.created_at,
            container=dict(
                name=self.link.name,
                cpu_usage=self.get_cpu_percentage(),
                memory_usage=self.get_memory_usage_in_mb()
            ) if self.link else None
        )
