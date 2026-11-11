from app.services.matches import catalog

async def get_players():
    return (await catalog())["players"]
