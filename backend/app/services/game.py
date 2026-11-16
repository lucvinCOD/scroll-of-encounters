from app.services.matches import catalog

async def get_games():
    return (await catalog())["games"]
