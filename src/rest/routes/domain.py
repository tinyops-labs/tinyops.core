from fastapi import APIRouter
from fastapi.responses import JSONResponse
from model.objects.atom import Atom
from persistence.tinyops_db import db
from ..examples import DOMAIN_RESPONSES


def create_domain_router() -> APIRouter:
    router = APIRouter()

    @router.get("", 
        summary="Get all domains",
        description="Returns all domains",
        response_class=JSONResponse, 
        responses=DOMAIN_RESPONSES["get"]
    )
    def get_all_domains():
        domains = Atom.get_domains()
        result = []
        for item in domains:
            result.append({
                "name": item["name"],
                "domain": item["domain"],
                "ssl": item["ssl"],
                "ssl_ready": db.get(item["domain"], "ssl_ready") or False,
                "ssl_pending": db.get(item["domain"], "ssl_pending") or False,
                "ssl_creation_failed": db.get(item["domain"], "ssl_creation_failed") or False
            })
        return result

    @router.post("/{domain}/reset-ssl-failed", response_class=JSONResponse, responses=DOMAIN_RESPONSES["reset"])
    def reset_ssl_creation_failed(domain: str):
        db.set(domain, "ssl_creation_failed", False)
        return True

    return router
