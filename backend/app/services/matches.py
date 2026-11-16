from app.db import rpc
from app.models import MatchRequest

async def catalog() -> dict:
    return await rpc("soe_catalog")

async def history(limit: int, offset: int, community_id: int | None) -> dict:
    return await rpc("soe_match_history", {"p_limit": limit, "p_offset": offset, "p_community": community_id})

async def register_match(body: MatchRequest, actor: str) -> dict:
    return await rpc("soe_register_match", {
        "p_actor": actor, "p_community": body.community_id, "p_format": body.format_id,
        "p_date": body.match_date.isoformat(), "p_start": body.approximate_start_time.isoformat(),
        "p_players": body.participant_ids, "p_draw": body.result.type == "draw",
        "p_winner": body.result.winner_player_id,
    })
