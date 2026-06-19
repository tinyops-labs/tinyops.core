import time
import subprocess
import os
import threading
import pathlib

from datetime import datetime
from persistence.tinyops_db import db
from modules.globals import Global
from utils.logger import info, error, critical
from modules.ssh_worker import SSHWorker
from utils.utils import Utils
from model.objects.atom import Atom


class GitWatcher:

    def __init__(self):
        self.repos = []
        self.repos_dir = pathlib.Path(os.path.expanduser("~")) / ".tinyops" / "repos"
        self.ssh_worker = SSHWorker()
        self.private_key_path = self.ssh_worker.private_key_path.as_posix()
        self.env = { "GIT_SSH_COMMAND": f"ssh -o StrictHostKeyChecking=no -i {self.private_key_path}" }

    def start(self):
        self._create_repos_directory()
        threading.Thread(target=self._sync).start()

    def _sync(self):
        info("Git watcher thread started")
        while Global.sync:
            try:
                self._update_repos_list()
                self._clone_repositories()
                self._check_if_new_revision_available()
            except Exception:
                pass
            time.sleep(2)

    def _update_repos_list(self):
        repos = db.get_list("repos")
        git_urls = Atom.get_git_urls()

        for repo in repos[:]:
            repo_url = repo.get("url")
            if repo_url not in git_urls:
                repos.remove(repo)

        db.set("repos", value=repos)
        self.repos = db.get_list("repos")

    def _create_repos_directory(self):
        self.repos_dir.mkdir(parents=True, exist_ok=True)

    def _check_if_new_revision_available(self):
        for repo in self.repos:
            url = repo.get("url")
            branch = repo.get("branch")
            repo_name = repo.get("repo_name")
            self._pull_repository(repo_name)
            current_local_revision = self._get_current_local_revision(repo_name)

            if current_local_revision != db.get(repo_name, "revision"):
                info(f"New revision available for {repo_name}, creating Pipeline...")
                db.set(repo_name, "revision", current_local_revision)
                db.append_to_list("pipelines", dict(
                    id=Utils.generate_random_string(16),
                    repo_name=repo_name,
                    git_url=url,
                    git_branch=branch,
                    directory=str(self.repos_dir / repo_name),
                    image_name=f"{repo_name}-{current_local_revision}",
                    created=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    finished=None,
                    duration=None,
                    log=None,
                    status="pending"
                ))

    def _get_current_local_revision(self, repo_name):
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repos_dir / repo_name,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def _pull_repository(self, repo_name):
        repo_path = self.repos_dir / repo_name
        result = subprocess.run(
            ["git", "pull"],
            cwd=repo_path,
            env=self.env,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            error(f"Failed to pull repository {repo_name}: {result.stderr.strip()}")

    def _clone_repositories(self):
        for repo in self.repos:
            try:
                url = repo.get("url")
                branch = repo.get("branch")
                repo_name = repo.get("repo_name")
                if not (self.repos_dir / repo_name).exists():
                    info(f"Cloning repository: {repo_name} from {url} (branch: {branch})")
                    result = subprocess.run(
                        ["git", "clone", "-b", branch, url, str(self.repos_dir / repo_name)],
                        env=self.env,
                        capture_output=True
                    )
                    if result.returncode != 0:
                        error(f"Failed to clone {repo_name}: {result.stderr.strip()}")
                    else:
                        info(f"Cloned repository: {repo_name} successfully")
            except Exception as e:
                critical(f"Unexpected error while cloning repository {url} (branch: {branch}): {e}")
