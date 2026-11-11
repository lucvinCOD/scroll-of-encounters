# Importa a classe FastAPI.
# ⚡ CLASSE EXTERNA: vem do pacote FastAPI instalado na .venv.
from fastapi import FastAPI

# Importa o objeto "router" criado em cards.py.
# 🧑‍💻 OBJETO NOSSO.
# Dentro deste arquivo, damos a ele o nome "cards_router".
from app.routers.cards import router as cards_router

# Importa o objeto "router" criado em games.py.
# 🧑‍💻 OBJETO NOSSO.
# Dentro deste arquivo, damos a ele o nome "games_router".
from app.routers.games import router as games_router
from app.routers.player import router as players_router
from app.routers.auth import router as auth_router
from app.routers.matches import router as matches_router


# 🧑‍💻 VARIÁVEL NOSSA: app.
# FastAPI() instancia a CLASSE FastAPI e retorna o objeto principal da nossa API.
app = FastAPI(
    title="Scroll of Encounters API",
    version="0.1.0"
)


# ⚡ DECORATOR do FastAPI.
# Registra uma rota HTTP GET para a raiz "/" da aplicação.
@app.get("/")
def root():
    return {
        "message": "Scroll of Encounters API is running"
    }


# ⚡app: objeto da classe FastAPI.
# include_router(): MÉTODO do objeto FastAPI "app".
# (cards_router): argumento que estamops passando para o MÉTODO include_router().
# Registra no aplicativo as rotas existentes dentro de cards_router.
app.include_router(cards_router)

# ⚡ MÉTODO do objeto FastAPI "app".
# Registra no aplicativo as rotas existentes dentro de games_router.
app.include_router(games_router)
app.include_router(players_router)

app.include_router(auth_router)
app.include_router(matches_router)
