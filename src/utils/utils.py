import random
import string
import psutil
import threading

from pathlib import Path


class Utils:
    _cpu_percent = 0.0
    _cpu_monitor_running = False
    _cpu_monitor_thread = None

    @classmethod
    def start_cpu_monitoring(cls):
        if not cls._cpu_monitor_running:
            cls._cpu_monitor_running = True
            cls._cpu_monitor_thread = threading.Thread(target=cls._cpu_monitor_worker, daemon=True)
            cls._cpu_monitor_thread.start()
    
    @classmethod
    def _cpu_monitor_worker(cls):
        """Background worker that updates CPU percentage every 2 seconds"""
        psutil.cpu_percent(interval=1)
        
        while cls._cpu_monitor_running:
            try:
                cls._cpu_percent = psutil.cpu_percent(interval=2)
            except Exception:
                cls._cpu_percent = 0.0

    @staticmethod
    def generate_random_string(length=64):
        return "".join(random.choice(string.digits + string.ascii_uppercase + string.ascii_lowercase) for _ in range(length))

    @staticmethod
    def extract_repo_name_from_git_url_and_branch(repo_url: str, branch: str = None) -> str:
        repo_url = repo_url.rstrip("/")
        name = repo_url.split("/")[-1].removesuffix('.git')
        if ":" in name:
            name = name.split(":")[-1]
        return f"{name}-{branch.replace('/', '-')}"

    @classmethod
    def get_cpu_usage_in_gb(cls):
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            total_ghz = cpu_count * cpu_freq.max / 1000
            cls.start_cpu_monitoring()
            used_percent = cls._cpu_percent
            used_ghz = total_ghz * used_percent / 100
            return f"{used_ghz:.1f}GB / {total_ghz:.0f}GB"
        else:
            return "N/A"


    @staticmethod
    def get_system_stats():
        return dict(
            ram_usage=Utils.get_ram_usage_in_gb(),
            cpu_usage_percent=Utils.get_cpu_usage_in_percent(),
            ram_usage_percent=Utils.get_ram_usage_in_percent(),
            number_of_cores=Utils.get_number_of_cores(),
            number_of_threads=Utils.get_number_of_threads()
        )

    @staticmethod
    def get_ram_usage_in_gb():
        ram = psutil.virtual_memory()
        return f"{ram.used / (1024 ** 3):.1f}GB / {ram.total / (1024 ** 3):.0f}GB"

    @classmethod
    def get_cpu_usage_in_percent(cls):
        return f"{cls._cpu_percent:.1f}"

    @staticmethod
    def get_ram_usage_in_percent():
        return f"{psutil.virtual_memory().percent}"

    @staticmethod
    def get_number_of_cores():
        return psutil.cpu_count(logical=True)

    @staticmethod
    def get_number_of_threads():
        return psutil.cpu_count(logical=False)

    @staticmethod
    def get_version():
        p = Path.cwd().parent / ".version"
        if not p.is_file():
            return "unknown"
        return p.read_text(encoding="utf-8").strip()


class DotDict(dict):
    def __getattr__(self, item):
        value = self.get(item)
        if isinstance(value, dict):
            value = DotDict(value)
            self[item] = value
        return value

