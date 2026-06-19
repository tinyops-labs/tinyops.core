import threading
import uvicorn

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP

from config.config import config
from utils.logger import info
from .routes.blueprint import create_blueprint_router
from .routes.container import create_container_router
from .routes.dashboard import create_dashboard_router
from .routes.system import create_system_router
from .routes.domain import create_domain_router
from .routes.pipeline import create_pipeline_router
from .routes.settings import create_settings_router


class RestAPI:

    def __init__(self, model, host='0.0.0.0', port=5000):
        self.model = model
        self.server = None
        self.server_thread = None
        self._running = False
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="TinyOps API",
            description="TinyOps REST API for container orchestration",
            version="1.0.0"
        )

        self._setup_middleware()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"],
        )
        self._setup_routes()
        self._mcp = FastApiMCP(self.app)
        self._mcp.mount_http()

    def _setup_middleware(self):
        @self.app.middleware("http")
        async def require_auth(request: Request, call_next):
            if request.method == "OPTIONS":
                return await call_next(request)
            h = request.headers.get("Authorization") or ""
            parts = h.split(None, 1)
            token = ((parts[1] if len(parts) == 2 else parts[0]) if parts else "").strip()
            if not config.auth_key or token != config.auth_key:
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            return await call_next(request)
    
    def _setup_routes(self):
        self.app.include_router(create_blueprint_router(self.model), prefix="/blueprint", tags=["Blueprint"])
        self.app.include_router(create_container_router(self.model), prefix="/container", tags=["Container"])
        self.app.include_router(create_dashboard_router(self.model), prefix="/dashboard", tags=["Dashboard"])
        self.app.include_router(create_system_router(self.model), prefix="/system", tags=["System"])
        self.app.include_router(create_domain_router(), prefix="/domain", tags=["Domain"])
        self.app.include_router(create_pipeline_router(), prefix="/pipeline", tags=["Pipeline"])
        self.app.include_router(create_settings_router(self.model), prefix="/settings", tags=["Settings"])

    def start(self):
        if not self._running:
            info("Starting TinyOps REST API...")
            self._running = True
            uvicorn_config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="warning")
            self.server = uvicorn.Server(uvicorn_config)
            self.server_thread = threading.Thread(target=self.server.run, daemon=True)
            self.server_thread.start()
            info(f"TinyOps REST API running at http://{self.host}:{self.port}")
            info(f"OpenAPI docs available at http://{self.host}:{self.port}/docs")
    
    def stop(self):
        if self._running:
            info("Stopping REST API server...")
            self._running = False
            
            if self.server:
                self.server.should_exit = True
            
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=2)
            
            info("REST API server stopped")
