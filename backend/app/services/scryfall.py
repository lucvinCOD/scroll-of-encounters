import httpx
from fastapi import HTTPException


SCRYFALL_URL = "https://api.scryfall.com/cards/named"

HEADERS = {
    "User-Agent": "ScrollOfEncounters/0.1",
    "Accept": "application/json;q=0.9,*/*;q=0.8"
}


async def search_card_by_name(name: str):
    params = {
        "fuzzy": name
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(SCRYFALL_URL, params=params, headers=HEADERS)
    except httpx.RequestError:
        raise HTTPException(503, "Busca de cartas temporariamente indisponível.") from None

    if response.status_code != 200:
        raise HTTPException(
            status_code=404 if response.status_code == 404 else 503,
            detail="Card not found" if response.status_code == 404 else "Busca de cartas temporariamente indisponível."
        )

    card = response.json()

    image = None

    if "image_uris" in card:
        image = card["image_uris"].get("normal")

    elif card.get("card_faces"):
        first_face = card["card_faces"][0]

        if "image_uris" in first_face:
            image = first_face["image_uris"].get("normal")

    return {
        "id": card["id"],
        "name": card["name"],
        "mana_cost": card.get("mana_cost"),
        "type_line": card.get("type_line"),
        "image": image
    }
