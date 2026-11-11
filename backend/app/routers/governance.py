from fastapi import APIRouter, Depends, Path, Query, Response

from app.auth import current_user
from app.models import DisputeResolution, ModeratorAssignment
from app.permissions import administrator, moderator, writing_administrator, writing_moderator
from app.services import governance


def no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(tags=["Permissions and moderation"], dependencies=[Depends(no_store)])


@router.get("/auth/permissions")
async def permissions(user: dict = Depends(current_user)):
    return {"role": user.get("role", "USER"), "moderated_community_ids": user.get("moderated_community_ids", [])}


@router.get("/admin/users")
async def list_users(q: str = Query("", max_length=80), limit: int = Query(30, ge=1, le=100),
                     offset: int = Query(0, ge=0), user: dict = Depends(administrator)):
    return await governance.users(user["id"], q, limit, offset)


@router.post("/admin/moderators")
async def assign_moderator(body: ModeratorAssignment, user: dict = Depends(writing_administrator)):
    return await governance.set_moderator(user["id"], str(body.profile_id), body.community_id, body.enabled, body.reason)


@router.get("/admin/audit")
async def list_audit(limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0),
                     user: dict = Depends(administrator)):
    return await governance.audit(user["id"], limit, offset)


@router.get("/moderation/matches")
async def list_disputes(community_id: int | None = Query(None, gt=0), limit: int = Query(30, ge=1, le=100),
                        offset: int = Query(0, ge=0), user: dict = Depends(moderator)):
    return await governance.disputes(user["id"], community_id, limit, offset)


@router.get("/moderation/matches/{match_id}")
async def match_dispute(match_id: int = Path(gt=0), user: dict = Depends(moderator)):
    return await governance.dispute(user["id"], match_id)


@router.post("/moderation/matches/{match_id}/resolution")
async def resolve_dispute(body: DisputeResolution, match_id: int = Path(gt=0), user: dict = Depends(writing_moderator)):
    return await governance.resolve(user["id"], match_id, body.decision, body.reason)
