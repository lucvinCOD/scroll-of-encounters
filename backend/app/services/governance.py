from app.db import rpc


async def users(actor: str, query: str, limit: int, offset: int) -> dict:
    return await rpc("soe_admin_users", {"p_actor": actor, "p_query": query, "p_limit": limit, "p_offset": offset})


async def set_moderator(actor: str, target: str, community: int, enabled: bool, reason: str) -> dict:
    return await rpc("soe_set_moderator", {
        "p_actor": actor, "p_target": target, "p_community": community,
        "p_enabled": enabled, "p_reason": reason,
    })


async def disputes(actor: str, community: int | None, limit: int, offset: int) -> dict:
    return await rpc("soe_moderation_matches", {
        "p_actor": actor, "p_community": community, "p_limit": limit, "p_offset": offset,
    })


async def dispute(actor: str, match_id: int) -> dict:
    return await rpc("soe_moderation_match", {"p_actor": actor, "p_match": match_id})


async def resolve(actor: str, match_id: int, decision: str, reason: str) -> dict:
    return await rpc("soe_resolve_dispute", {
        "p_actor": actor, "p_match": match_id, "p_decision": decision, "p_reason": reason,
    })


async def audit(actor: str, limit: int, offset: int) -> dict:
    return await rpc("soe_admin_audit", {"p_actor": actor, "p_limit": limit, "p_offset": offset})
