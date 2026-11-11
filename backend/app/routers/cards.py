from fastapi import APIRouter
from app.services.scryfall import search_card_by_name


router = APIRouter(
    prefix="/cards",
    tags=["Cards"]
)


@router.get("/search")
async def search_card(name: str):
    return await search_card_by_name(name)