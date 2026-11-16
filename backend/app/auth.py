from uuid import UUID
import httpx
from fastapi import HTTPException, Request, Response
from app.config import cookie_secure, supabase_config, trusted_origins
from app.db import rpc

ACCESS_COOKIE = "soe_access"
REFRESH_COOKIE = "soe_refresh"

def check_origin(request: Request) -> None:
    if request.headers.get("origin") not in trusted_origins():
        raise HTTPException(403, "Origem da requisição não autorizada.")

async def auth_request(path: str, *, token: str | None = None, body: dict | None = None, method: str | None = None):
    url, key = supabase_config()
    headers = {"apikey": key}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(method or ("POST" if body is not None else "GET"), f"{url}/auth/v1/{path}", headers=headers, json=body)
    except httpx.RequestError:
        raise HTTPException(503, "Serviço de autenticação indisponível.") from None
    if not response.is_success:
        if response.status_code == 429:
            raise HTTPException(429, "Aguarde um momento antes de tentar entrar novamente.")
        if response.status_code >= 500:
            raise HTTPException(503, "Serviço de autenticação indisponível.")
        raise HTTPException(401, "Sessão expirada ou credenciais inválidas.")
    return response.json() if response.content else {}

async def authenticated_actor(request: Request) -> str:
    bearer = request.headers.get("authorization", "")
    token = bearer[7:] if bearer.startswith("Bearer ") else request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(401, "Entre na sua conta para continuar.")
    user = await auth_request("user", token=token)
    try:
        actor = str(UUID(user["id"]))
    except (ValueError, KeyError, TypeError):
        raise HTTPException(401, "Sessão inválida.") from None
    return actor

async def current_user(request: Request) -> dict:
    return await rpc("soe_identity", {"p_actor": await authenticated_actor(request)})

async def writing_actor(request: Request) -> str:
    if not request.headers.get("authorization", "").startswith("Bearer "):
        check_origin(request)
    return await authenticated_actor(request)

async def writing_user(request: Request) -> dict:
    if not request.headers.get("authorization", "").startswith("Bearer "):
        check_origin(request)
    user = await current_user(request)
    if user.get("needs_profile"):
        raise HTTPException(403, "Complete seu perfil e comunidade principal antes de registrar.")
    return user

def set_session(response: Response, session: dict) -> None:
    response.set_cookie(ACCESS_COOKIE, session["access_token"], httponly=True, secure=cookie_secure(), samesite="lax", max_age=int(session.get("expires_in", 3600)), path="/")
    response.set_cookie(REFRESH_COOKIE, session["refresh_token"], httponly=True, secure=cookie_secure(), samesite="lax", max_age=30*24*3600, path="/")

def clear_session(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")
