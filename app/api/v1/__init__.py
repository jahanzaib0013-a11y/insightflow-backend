"""Version-1 API barrel: one router that carries every feature router.

main.py mounts only this; new feature routers get added here
(the FastAPI equivalent of a Node routes/index.js).
"""

from fastapi import APIRouter

from app.api.v1 import auth, oauth

router = APIRouter()
router.include_router(auth.router)
router.include_router(oauth.router)
