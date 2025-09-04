from fastapi import APIRouter

from .pages import table


router = APIRouter()

router.include_router(table.router)
