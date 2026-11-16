# Importa a classe APIRouter do FastAPI.
# ⚡ CLASSE EXTERNA: vem do pacote FastAPI instalado na .venv.
# Ela permite criar e organizar um conjunto de rotas separado do main.py.
from fastapi import APIRouter

# Importa a função get_games() que NÓS criamos em services/game.py.
# 🧑‍💻 FUNÇÃO NOSSA: consulta a tabela "game" através do cliente Supabase.
from app.services.game import get_games


# 🧑‍💻 VARIÁVEL NOSSA: "router".
# APIRouter() é a instanciação da CLASSE APIRouter do FastAPI.
# O objeto resultante armazenará as rotas relacionadas a games.
router = APIRouter(
    prefix="/games",
    tags=["Games"]
)


# ⚡ DECORATOR do FastAPI.
# Define que uma requisição HTTP GET para "/games" executará a função list_games() abaixo.
# LEIA COMO: "Quando houver uma requisição GET para a rota /games, execute a função list_games()".
# @ é sintaxe do python e indica aplicação de um decorator à função/classe seguinte.
# No Scroll, estamos usando decorators do FastAPI para associar funções Python às rotas HTTP.
# router.get("/") é método do objeto APIRouter do FastAPI.
# Como o prefixo "/games" já foi definido no APIRouter, usamos apenas "/" aqui.
@router.get("/")
async def list_games():

    # Chama a FUNÇÃO NOSSA get_games(), importada de services/game.py.
    # Ela consulta o Supabase e retorna os registros da tabela "game".
    return await get_games()