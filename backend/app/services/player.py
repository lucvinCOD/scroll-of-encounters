# Importa o objeto "supabase" criado em app/db.py.
# 🧑‍💻 OBJETO NOSSO: cliente configurado para acessar nosso projeto Supabase.
from app.db import supabase


# 🧑‍💻 FUNÇÃO NOSSA: busca todos os jogadores cadastrados.
def get_players():

    # 🧑‍💻 VARIÁVEL NOSSA: recebe o objeto de resposta retornado pelo Supabase.
    #
    # .table("player") → MÉTODO do cliente Supabase que seleciona a tabela "player".
    # .select("*")     → MÉTODO que solicita todas as colunas.
    # .execute()       → MÉTODO que executa a consulta.
    response = (
        supabase
        .table("player")
        .select("*")
        .execute()
    )

    # .data é um ATRIBUTO do objeto "response".
    # Contém os registros retornados pelo banco.
    return response.data