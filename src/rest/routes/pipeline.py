from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..examples import PIPELINE_RESPONSES
from persistence.tinyops_db import db


def create_pipeline_router() -> APIRouter:
    router = APIRouter()

    @router.get("", 
        summary="Get all pipelines",
        description="Returns all pipelines",
        response_class=JSONResponse, 
        responses=PIPELINE_RESPONSES["get"]
    )
    def get_all_pipelines():
        return db.get_list("pipelines")[:100]

    return router
