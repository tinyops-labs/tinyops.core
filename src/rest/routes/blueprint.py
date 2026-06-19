from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from parser.blueprint_validator import BlueprintValidationError
from ..examples import BLUEPRINT_RESPONSES


def create_blueprint_router(model) -> APIRouter:
    router = APIRouter()

    @router.get("", response_class=JSONResponse, responses=BLUEPRINT_RESPONSES["get"])
    def get_blueprint():
        return model.api_service.get_blueprint()

    @router.post("", 
        summary="Update the blueprint",
        description="Updates the blueprint with the given data",
        response_class=JSONResponse, 
        responses=BLUEPRINT_RESPONSES["post"],
    )
    def update_blueprint(data: dict):
        try:
            return model.api_service.update_blueprint(data)
        except BlueprintValidationError as e:
            raise HTTPException(status_code=400, detail={"errors": e.errors}) from e

    return router
