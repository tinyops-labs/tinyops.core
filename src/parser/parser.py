import yaml

from config.config import config
from utils.utils import DotDict
from utils.logger import error


class Parser:

    def __init__(self, test=False):
        self._blueprint = dict()
        self._test = test

    @property
    def applications(self):
        return self._blueprint.get("applications") or []

    @property
    def blueprint(self):
        return self._blueprint

    def load_blueprint(self):
        if config.gitops_url == "local":
            blueprint = self._load_blueprint_from_local()
        else:
            blueprint = self._load_blueprint_from_git_repo()
        if not self._test:
            self._blueprint = blueprint

    def add_to_blueprint(self, application):
        if self._blueprint.get("applications"):
            self._blueprint["applications"].append(application)

    def _load_blueprint_from_local(self):
        try:
            with open("../blueprint.yaml", 'r') as settings:
                return DotDict(yaml.load(settings, Loader=yaml.Loader))
        except Exception as e:
            error(f"Blueprint parsing Error: {e}")

    def _load_blueprint_from_git_repo(self):
        return dict(applications=[])

    def update_blueprint_file(self, data):
        raw = yaml.dump(
            {"applications": data.get("applications") or []},
            default_flow_style=False,
            sort_keys=False,
            indent=2,
            allow_unicode=True,
        ).rstrip("\n")
        lines = raw.split("\n")
        out = []
        seen_root_item = False
        for line in lines:
            if line.startswith("- "):
                if seen_root_item:
                    out.append("")
                seen_root_item = True
            out.append(line)
        with open("../blueprint.yaml", "w", encoding="utf-8", newline="\n") as settings:
            settings.write("\n".join(out) + "\n")
