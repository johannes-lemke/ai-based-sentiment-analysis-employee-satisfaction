from fastapi import APIRouter

from src.routes import (
    admin_feedback,
    auth,
    categories,
    dashboard,
    locations,
    maintenance,
    pages,
    public_feedback,
)

# Sammelt alle Endpunkt-Router. main.py bindet nur noch diesen einen Router ein.
api_router = APIRouter()
api_router.include_router(pages.router)
api_router.include_router(auth.router)
api_router.include_router(public_feedback.router)
api_router.include_router(admin_feedback.router)
api_router.include_router(dashboard.router)
api_router.include_router(categories.router)
api_router.include_router(locations.router)
api_router.include_router(maintenance.router)
