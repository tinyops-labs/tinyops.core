from model.objects.atom import Atom
from utils.utils import Utils
from modules.ssh_worker import SSHWorker
from parser.blueprint_validator import BlueprintValidator, BlueprintValidationError


class ApiService:

    def __init__(self, model):
        self.model = model

    def get_current_state(self):
        return dict(
            atoms=[atom.__dict__() for atom in self.model.atoms],
            networks=[network.__dict__() for network in self.model.networks],
            blueprint=self.model._parser.blueprint,
            system_stats=Utils.get_system_stats()
        )

    def get_container_logs_by_id(self, atom_id):
        if atom_id == "TINYOPS_GATEWAY":
            return Atom.get_gateway_atom().get_container_logs()
        atom = Atom.get_by_id(atom_id)
        return atom.get_container_logs()

    def get_blueprint(self):
        return self.model._parser._load_blueprint_from_local()

    def update_blueprint(self, data):
        errors = BlueprintValidator(data).validate()
        if errors:
            raise BlueprintValidationError(errors)
        self.model._parser.update_blueprint_file(data)
        return True

    def get_ssh_public_key(self):
        return SSHWorker().retrieve_public_key()