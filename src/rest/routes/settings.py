from fastapi import APIRouter
from fastapi.responses import JSONResponse
from persistence.tinyops_db import db
from ..examples import SETTINGS_RESPONSES


def create_settings_router(model) -> APIRouter:
    router = APIRouter()

    @router.get("", 
        summary="Get the settings",
        description="Returns the settings",
        response_class=JSONResponse, 
        responses=SETTINGS_RESPONSES["get"]
    )
    def get_settings():
        return {
            "ssh_public_key": model.api_service.get_ssh_public_key(),
            "database": db.internal_snapshot(),
        }

    return router
