"""Papéis vêm do banco a cada requisição, nunca de campos enviados pelo cliente."""
from fastapi import Depends, HTTPException

from app.auth import current_user, writing_user


def check_role(user: dict, allowed: set[str]) -> dict:
    if user.get("needs_profile") or user.get("role", "USER") not in allowed:
        raise HTTPException(403, "Sua conta não tem permissão para esta operação.")
    return user


async def moderator(user: dict = Depends(current_user)) -> dict:
    return check_role(user, {"MODERATOR", "ADMIN"})


async def writing_moderator(user: dict = Depends(writing_user)) -> dict:
    return check_role(user, {"MODERATOR", "ADMIN"})


async def administrator(user: dict = Depends(current_user)) -> dict:
    return check_role(user, {"ADMIN"})


async def writing_administrator(user: dict = Depends(writing_user)) -> dict:
    return check_role(user, {"ADMIN"})
