from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..examples import DASHBOARD_RESPONSES


def create_dashboard_router(model) -> APIRouter:
    router = APIRouter()

    @router.get("", 
        summary="Get the dashboard data",
        description="Returns the dashboard data, including atoms, networks, and system stats",
        response_class=JSONResponse, 
        responses=DASHBOARD_RESPONSES
    )
    def dashboard():
        return model.api_service.get_current_state()

    return router
