import subprocess
import threading
import time
import traceback

from datetime import datetime
from persistence.tinyops_db import db
from utils.logger import info, error, critical
from modules.globals import Global

class Pipeline:

    def __init__(self):
        self.pipelines = []

    def start(self):
        threading.Thread(target=self._sync).start()

    def _sync(self):
        info("Pipeline thread started")
        while Global.sync:
            try:
                self.pipelines = db.get_list("pipelines")
                self._build_docker_images()
            except Exception:
                pass
            time.sleep(2)

    def _get_pipelines_ready_to_run(self):
        return [pipeline for pipeline in self.pipelines if pipeline["status"] == "pending"]

    def _build_docker_images(self):
        for pipeline in self._get_pipelines_ready_to_run():
            try:
                self._build_docker_image(pipeline)
            except Exception:
                critical(f"Unexpected error while building docker image for {pipeline.get('image_name')}: {traceback.format_exc()}")

    def _build_docker_image(self, pipeline):
        info(f"Building docker image for {pipeline['image_name']}")
        result = subprocess.run(
            ["docker", "build", "-t", pipeline['image_name'], "."],
            cwd=pipeline['directory'],
            capture_output=True,
            text=True
        )
        pipeline['log'] = (result.stdout.strip() + "\n" + result.stderr.strip()).strip()
        if result.returncode != 0:
            error(f"Failed to build docker image for {pipeline['image_name']}: {result.stderr.strip()}")
            pipeline['status'] = "failed"
        else:
            info(f"Built docker image for {pipeline['image_name']}")
            pipeline['status'] = "success"
            db.set(pipeline['repo_name'], "image_name", value=pipeline['image_name'])
        pipeline['finished'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pipeline['duration'] = (datetime.now() - datetime.strptime(pipeline['created'], "%Y-%m-%d %H:%M:%S")).total_seconds()
        self._save_pipeline(pipeline)

    def _save_pipeline(self, pipeline):
        for p in self.pipelines:
            if p['id'] == pipeline['id']:
                p = pipeline
                break
        db.set("pipelines", value=self.pipelines)

