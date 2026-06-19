import re


class BlueprintValidationError(Exception):

    def __init__(self, errors):
        self.errors = errors


class BlueprintValidator:

    ENV_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

    def __init__(self, body):
        self.body = body if isinstance(body, dict) else None

    def validate(self):
        errors = []
        if self.body is None:
            errors.append("Request body must be a JSON object.")
            return errors
        apps = self.body.get("applications")
        if apps is None:
            apps = []
        if not isinstance(apps, list):
            errors.append("applications must be a list.")
            return errors
        for idx, app in enumerate(apps):
            label = f"applications[{idx}]"
            if not isinstance(app, dict):
                errors.append(f"{label}: each application must be an object.")
                continue
            name = app.get("name")
            if not name or not isinstance(name, str):
                errors.append(f"{label}: name is required and must be a non-empty string.")
            ref = name if isinstance(name, str) and name else label
            git = app.get("git")
            image = app.get("image")
            if git is not None:
                if not isinstance(git, dict):
                    errors.append(f"Application {ref}: git must be an object with url (and optional branch).")
                else:
                    url = git.get("url")
                    if not url or not isinstance(url, str):
                        errors.append(f"Application {ref}: git.url is required and must be a non-empty string.")
            elif not image or not isinstance(image, str) or not image.strip():
                errors.append(f"Application {ref}: image is required unless git is set.")
            if "replicas" in app and app["replicas"] is not None:
                r = app["replicas"]
                if type(r) is not int or r < 0:
                    errors.append(f"Application {ref}: replicas must be a non-negative integer.")
            network = app.get("network")
            if network is not None and network != "":
                if not isinstance(network, str) or not network.strip():
                    errors.append(f"Application {ref}: network must be a non-empty string when set.")
            env = app.get("env")
            if env is not None:
                if not isinstance(env, dict):
                    errors.append(f"Application {ref}: env must be an object.")
                else:
                    for k, v in env.items():
                        if not isinstance(k, str) or not self.ENV_KEY_PATTERN.match(k):
                            errors.append(f"Application {ref}: invalid env key {k!r}.")
                        if v is not None and not isinstance(v, (str, int, bool)):
                            errors.append(f"Application {ref}: env value for {k!r} must be a string, integer, boolean, or null.")
            ports = app.get("ports")
            if ports is not None:
                if not isinstance(ports, dict):
                    errors.append(f"Application {ref}: ports must be an object.")
                else:
                    for container_port, host_port in ports.items():
                        try:
                            cpi = int(container_port)
                            if not (1 <= cpi <= 65535):
                                errors.append(f"Application {ref}: container port {container_port!r} must be between 1 and 65535.")
                        except (ValueError, TypeError):
                            errors.append(f"Application {ref}: container port {container_port!r} must be a valid port number.")
                        if host_port is not None:
                            try:
                                hpi = int(host_port)
                                if not (1 <= hpi <= 65535):
                                    errors.append(f"Application {ref}: host port {host_port!r} must be between 1 and 65535.")
                            except (ValueError, TypeError):
                                errors.append(f"Application {ref}: host port {host_port!r} must be a valid port number or null.")
            ports = app.get("ports")
            replicas = app.get("replicas", 1)
            if ports and isinstance(ports, dict) and len(ports) > 0:
                if type(replicas) is int and replicas > 1:
                    errors.append(f"Application {ref}: cannot use port mappings with more than one replica.")
            vols = app.get("volumes")
            if vols is not None:
                if not isinstance(vols, list):
                    errors.append(f"Application {ref}: volumes must be a list.")
                else:
                    for i, item in enumerate(vols):
                        if not isinstance(item, str) or not item.strip():
                            errors.append(f"Application {ref}: volumes[{i}] must be a non-empty string.")
            if "ssl" in app and app["ssl"] is not None and not isinstance(app["ssl"], bool):
                errors.append(f"Application {ref}: ssl must be a boolean when set.")
            domain = app.get("domain")
            if domain is not None and domain != "" and not isinstance(domain, str):
                errors.append(f"Application {ref}: domain must be a string when set.")
        return errors
