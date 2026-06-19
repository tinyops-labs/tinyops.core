from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..examples import CONTAINER_RESPONSES


def create_container_router(model) -> APIRouter:
    router = APIRouter()

    @router.get("/logs/{_id}", 
        summary="Get the container logs",
        description="Returns the container logs for the given container ID",
        response_class=JSONResponse, 
        responses=CONTAINER_RESPONSES["logs"]
    )
    def container_logs(_id: str):
        return model.api_service.get_container_logs_by_id(_id)

    return router
