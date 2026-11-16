# Importa a classe APIRouter do FastAPI.
# ⚡ CLASSE EXTERNA: vem do pacote FastAPI instalado na .venv.
# Ela permite criar e organizar um conjunto de rotas separado do main.py.
from fastapi import APIRouter

# Importa a função get_players() que NÓS criamos em services/player.py.
# 🧑‍💻 FUNÇÃO NOSSA: consulta a tabela "player" através do cliente Supabase.
from app.services.player import get_players

# 🧑‍💻 VARIÁVEL NOSSA: "router".
# APIRouter() é a instanciação da CLASSE APIRouter do FastAPI.
# O objeto resultante armazenará as rotas relacionadas a players.
router = APIRouter(
    prefix="/players",
    tags=["Players"]
)


# Define que uma requisição HTTP GET para "/players" executará esta função.
# O prefixo "/players" já está definido no APIRouter, por isso a rota usa "/".
@router.get("/")
async def list_players():
    # Chama a função get_players() que NÓS criamos em services/player.py.
    # Ela retorna todos os jogadores cadastrados no banco de dados.
    # O resultado é retornado como resposta da requisição HTTP GET,.
    return await get_players()
