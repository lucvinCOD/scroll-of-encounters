"""Transporte assíncrono da Supabase Data API, exclusivo do servidor."""
import httpx
from fastapi import HTTPException
from app.config import supabase_config

MESSAGES = {
    "SOE_ACCESS_DENIED": "Sua conta não tem permissão para acessar estes registros.",
    "SOE_SELF_REVIEW": "Você não pode decidir uma disputa de partida que publicou ou da qual participou. Encaminhe para outra pessoa autorizada.",
    "SOE_REASON_REQUIRED": "Informe uma justificativa entre 10 e 2000 caracteres.",
    "SOE_INVALID_DECISION": "Escolha validar o registro ou cancelar a partida.",
    "SOE_INVALID_REFERENCE": "Confira o usuário e a comunidade selecionados.",
    "SOE_DISPUTE_CHANGED": "Esta disputa já mudou de estado. Atualize a página antes de continuar.",
    "SOE_PROFILE_NAME": "O nome público deve ter entre 3 e 40 caracteres.",
    "SOE_USERNAME_UNAVAILABLE": "Esse nome público já está em uso. Escolha outro.",
    "SOE_TEMPORAL_CONFLICT": "Um participante já possui partida com início a menos de 10 minutos deste horário.",
    "SOE_PARTICIPANT_COUNT": "A quantidade de participantes não atende ao formato selecionado.",
    "SOE_DUPLICATE_PLAYER": "Um jogador não pode aparecer duas vezes na mesma partida.",
    "SOE_INVALID_PARTICIPANTS": "Selecione participantes existentes e distintos.",
    "SOE_INVALID_RESULT": "Informe um único vencedor participante ou empate da mesa.",
    "SOE_START_REQUIRED": "Informe data e horário aproximado de início.",
    "SOE_ACTOR_FORBIDDEN": "Sua conta não possui um perfil ativo neste projeto.",
    "SOE_FORMAT_NOT_FOUND": "Formato não encontrado.",
    "SOE_GUEST_NAME": "O nome do convidado deve ter entre 2 e 80 caracteres.",
}

async def rpc(name: str, parameters: dict | None = None):
    url, key = supabase_config()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{url}/rest/v1/rpc/{name}", json=parameters or {}, headers={"apikey": key, "Authorization": f"Bearer {key}"})
    except httpx.RequestError:
        raise HTTPException(503, "Não foi possível conectar ao banco. Tente novamente.") from None
    if not response.is_success:
        try:
            error = response.json()
        except ValueError:
            error = {}
        code, message = error.get("code", ""), error.get("message", "")
        if message in MESSAGES:
            status = 409 if code in ("23P01", "40001") else 403 if code == "42501" else 422
            raise HTTPException(status, {"code": message, "message": MESSAGES[message]})
        if code in ("40001", "40P01", "55P03"):
            raise HTTPException(409, "Outra operação alterou os participantes. Tente novamente.")
        if code in ("23503", "23505", "23514"):
            raise HTTPException(422, "Referências ou resultado inválidos. Atualize a página e confira os dados.")
        raise HTTPException(503, "Banco indisponível ou migração de acesso ainda pendente.")
    return response.json()
