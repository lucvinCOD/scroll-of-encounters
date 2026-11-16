from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.auth import ACCESS_COOKIE, REFRESH_COOKIE, auth_request, check_origin, clear_session, current_user, set_session, writing_actor
from app.db import rpc
from app.models import LoginRequest, ProfileRequest, SessionRequest, EmailRequest, PasswordRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/session")
async def accept_confirmed_session(body: SessionRequest, request: Request, response: Response):
    check_origin(request)
    verified = await auth_request("user", token=body.access_token.get_secret_value())
    session = await auth_request("token?grant_type=refresh_token", body={"refresh_token": body.refresh_token.get_secret_value()})
    if verified["id"] != session["user"]["id"]:
        raise HTTPException(401, "Sessão inválida.")
    identity = await rpc("soe_identity", {"p_actor": verified["id"]})
    set_session(response, session)
    response.headers["Cache-Control"] = "no-store"
    return identity

@router.post("/recover", status_code=202)
async def recover(body: EmailRequest, request: Request):
    check_origin(request)
    await auth_request("recover", body={"email": body.email})
    return {"message": "Se houver uma conta com esse e-mail, você receberá um link para recuperar o acesso."}

@router.post("/password", status_code=204)
async def change_password(body: PasswordRequest, request: Request, response: Response, actor: str = Depends(writing_actor)):
    password = body.password.get_secret_value()
    if len(password) < 8:
        raise HTTPException(422, "Use uma senha com pelo menos oito caracteres.")
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        header = request.headers.get("authorization", "")
        token = header[7:] if header.startswith("Bearer ") else None
    await auth_request("user", token=token, body={"password": password}, method="PUT")
    clear_session(response)

@router.post("/signup", status_code=201)
async def signup(body: LoginRequest, request: Request, response: Response):
    check_origin(request)
    password = body.password.get_secret_value()
    if len(password) < 8:
        raise HTTPException(422, "Use uma senha com pelo menos oito caracteres.")
    try:
        session = await auth_request("signup", body={"email": body.email, "password": password})
    except HTTPException as error:
        if error.status_code == 401:
            raise HTTPException(400, "Não foi possível criar a conta. Confira os dados; se já tem uma conta, entre nela.") from None
        raise
    if session.get("access_token"):
        set_session(response, session)
        return {"confirmation_required": False, "user": await rpc("soe_identity", {"p_actor": session["user"]["id"]})}
    return {"confirmation_required": True}

@router.post("/profile")
async def complete_profile(body: ProfileRequest, actor: str = Depends(writing_actor)):
    return await rpc("soe_complete_profile", {"p_actor": actor, "p_username": body.username, "p_community": body.community_id})

@router.post("/login")
async def login(body: LoginRequest, request: Request, response: Response):
    check_origin(request)
    session = await auth_request("token?grant_type=password", body={"email": body.email, "password": body.password.get_secret_value()})
    identity = await rpc("soe_identity", {"p_actor": session["user"]["id"]})
    set_session(response, session)
    response.headers["Cache-Control"] = "no-store"
    return identity

@router.get("/me")
async def me(response: Response, user: dict = Depends(current_user)):
    response.headers["Cache-Control"] = "no-store"
    return user

@router.post("/refresh")
async def refresh(request: Request, response: Response):
    check_origin(request)
    if not request.cookies.get(REFRESH_COOKIE):
        raise HTTPException(401, "Entre na sua conta para continuar.")
    session = await auth_request("token?grant_type=refresh_token", body={"refresh_token": request.cookies.get(REFRESH_COOKIE, "")})
    identity = await rpc("soe_identity", {"p_actor": session["user"]["id"]})
    set_session(response, session)
    response.headers["Cache-Control"] = "no-store"
    return identity

@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response):
    check_origin(request)
    clear_session(response)
