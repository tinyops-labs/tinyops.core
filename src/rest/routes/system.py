from fastapi import APIRouter
from fastapi.responses import JSONResponse
from utils.logger import get_log_file_path
from utils.utils import Utils
from ..examples import SYSTEM_RESPONSES
from persistence.tinyops_db import db


def create_system_router(model) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/version", 
        summary="Get the version of the application",
        description="Returns the version of the application",
        response_class=JSONResponse, 
        responses=SYSTEM_RESPONSES["version"]
    )
    def get_version():
        return {"version": Utils.get_version()}

    @router.get(
        "/logs", 
        summary="Get the system logs",
        description="Returns the system logs",
        response_class=JSONResponse, 
        responses=SYSTEM_RESPONSES["logs"]
    )
    def get_system_logs(lines: int = 100):
        log_file = get_log_file_path()
        if not log_file.exists():
            return []
        
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return [line.rstrip("\n") for line in all_lines[-lines:]]

    @router.get(
        "/db", 
        summary="Get the database dump",
        description="Returns the database dump",
        response_class=JSONResponse, 
        responses=SYSTEM_RESPONSES["db"]
    )
    def get_db():
        return db.dump_db()

    @router.get("/public-key", 
        summary="Get the SSH public key",
        description="Returns the SSH public key",
        response_class=JSONResponse, 
        responses=SYSTEM_RESPONSES["public_key"]
    )
    def get_public_key():
        return model.api_service.get_ssh_public_key()

    return router
