import os
import io
import tarfile

from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from utils.logger import info, error, debug, critical
from model.objects.atom import Atom
from persistence.tinyops_db import db


class Gateway:

    def __init__(self):
        self.config_path = os.path.abspath("../generated_configs")
        self.template_path = os.path.abspath("../templates")
        self.config_hash = None
        os.makedirs(self.config_path, exist_ok=True)
    
    def get_applications(self):
        apps = {}
        for atom in Atom.atoms:
            if not atom.up_for_deletion and atom.name != "TINYOPS_GATEWAY" and atom.link:
                port = 80
                if atom.ports:
                    port = str(list(atom.ports.keys())[0]).strip('"\'')
                
                if atom.name not in apps:
                    apps[atom.name] = {
                        'upstreams': [],
                        'domain': getattr(atom, 'domain', None),
                        'ssl': atom.ssl,
                        'ssl_ready': db.get(str(atom.domain), "ssl_ready")
                    }
                
                apps[atom.name]['upstreams'].append({
                    'atom_name': f"{atom.link.name}",
                    'atom_port': port,
                    'atom_id': atom.id
                })
        return apps
    
    def generate_config(self):
        try:
            env = Environment(loader=FileSystemLoader(self.template_path))
            template = env.get_template("nginx.conf.template.ssl")
            
            return template.render({
                'applications': self.get_applications(),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception as e:
            error(f"Template error: {e}")
            return self._fallback_config()
    
    def _fallback_config(self):
        return """events { worker_connections 1024; }
                http {
                    server {
                        listen 80;
                        location /health { return 200 "Gateway Error"; }
                        location / { return 503 "TinyOps Gateway Error"; }
                    }
                }"""
    
    def update_config(self):
        config = self.generate_config()
        config_hash = hash(config)
        
        if self.config_hash != config_hash:
            self.config_hash = config_hash
            info("Updating gateway config")
            config_file = os.path.join(self.config_path, "nginx.conf")
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config)
            debug(f"Config written to {config_file}")
            return True
        return False

    def load_config_to_the_gateway_container(self, container):
        debug("Transferring nginx.conf to gateway container...")
        try:
            local_file = self.get_config_file_path()
            tarstream = io.BytesIO()
            with tarfile.open(fileobj=tarstream, mode='w') as tar:
                tar.add(local_file, arcname="nginx.conf")
            tarstream.seek(0)
            container.put_archive("/etc/nginx", tarstream)
            debug("Transferred nginx.conf to gateway container.")
        except Exception as e:
            critical(F"Failed to transfer nginx.conf to gateway container! - {e}")

    def create_ssl_certificate(self, domain, container):
        info(f"Creating SSL certificate for {domain}")

        cmd = [
            "certbot", "certonly",
            "--webroot", "-w", "/usr/share/nginx/html",
            "-d", domain,
            "--non-interactive",
            "--agree-tos",
            "--register-unsafely-without-email",
        ]

        try:
            exit_code, output = container.exec_run(cmd, tty=True)
            output_text = output.decode()
            if exit_code != 0:
                db.set(domain, "ssl_creation_failed", True)
                db.set(domain, "ssl_ready", False)
                error(f"Error creating SSL certificate for {domain}. Exit code: {exit_code}.")
                debug(f"SSL error output: {output_text}")
            else:
                db.set(domain, "ssl_ready", True)
                info(f"SSL certificate created successfully for {domain}")
        except Exception as e:
            critical(f"Error creating SSL certificate {e}")

    def get_config_file_path(self):
        path = os.path.join(self.config_path, "nginx.conf")
        debug(f"Nginx Config path: {path}")
        return path
    
    def reload_nginx(self, gateway_atom):
        try:
            result = gateway_atom.link.exec_run("nginx -s reload")
            debug(f"Nginx reload result: {result}")
            if result.exit_code != 0:
                error(f"Nginx reload failed: {result}")
        except Exception as e:
            error(f"Hot reload error: {e}")
