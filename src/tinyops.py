import signal
import sys
import time

from modules.ssh_worker import SSHWorker
from modules.globals import Global
from modules.git_watcher import GitWatcher
from modules.pipeline import Pipeline
from parser.parser import Parser
from model.model import Model
from controller.controller import Controller
from rest.rest import RestAPI
from utils.logger import info
from utils.utils import Utils


def main():
    info("Starting TinyOps...")
    info(f"TinyOps Version {Utils.get_version()}")

    SSHWorker().create_ssh_pair_if_not_exist()
    GitWatcher().start()
    Pipeline().start()
    parser = Parser()
    model = Model(parser=parser)
    controller = Controller(model=model)
    rest_api = RestAPI(model=model)

    def signal_handler(sig, frame):
        info("Stopping TinyOps...")
        Global.sync = False
        controller.stop()
        rest_api.stop()
        info("Stopped TinyOps")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        controller.start()
        rest_api.start()
        info("TinyOps running! Press Ctrl+C to stop.")
        
        while True:
            try:
                signal.pause()
            except AttributeError:
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
