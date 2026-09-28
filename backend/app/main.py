from fastapi import FastAPI

from app.routers.cards import router as cards_router


app = FastAPI(
    title="Communities API",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "Communities API is running"
    }


app.include_router(cards_router)