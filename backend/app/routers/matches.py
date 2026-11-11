from fastapi import APIRouter, Depends, Query
from app.auth import writing_user
from app.models import GuestRequest, MatchRequest
from app.services.matches import catalog, history, register_match
from app.db import rpc

router = APIRouter(tags=["Encounters"])

@router.get("/catalog")
async def get_catalog():
    return await catalog()

@router.get("/communities/")
async def list_communities():
    return (await catalog())["communities"]

@router.get("/formats/")
async def list_formats():
    return (await catalog())["formats"]

@router.get("/matches/")
async def list_matches(limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0), community_id: int | None = Query(None, gt=0)):
    return await history(limit, offset, community_id)

@router.post("/matches", status_code=201)
async def create_match(body: MatchRequest, user: dict = Depends(writing_user)):
    return await register_match(body, user["id"])

@router.post("/players/guests", status_code=201)
async def create_guest(body: GuestRequest, user: dict = Depends(writing_user)):
    return await rpc("soe_create_guest", {"p_actor": user["id"], "p_name": body.display_name, "p_community": body.community_id})
