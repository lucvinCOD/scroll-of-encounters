# Importa o objeto "supabase" que criamos em app/db.py.
# 🧑‍💻 OBJETO NOSSO: contém o cliente configurado para acessar nosso projeto Supabase.
from app.db import supabase


# 🧑‍💻 FUNÇÃO NOSSA: criada para buscar todos os jogos cadastrados no banco.
def get_games():

    # response: 🧑‍💻 VARIÁVEL NOSSA armazenará a resposta recebida do Supabase.
    # supabase: 🧑‍💻 OBJETO criado em db.py através da função create_client().
    # .table("game"):🗄️ MÉTODO do cliente Supabase. Informa que queremos trabalhar com a tabela chamada "game".
    # .select("*"):🗄️ MÉTODO da biblioteca Supabase. Define uma consulta que seleciona todas (*) as colunas.
    # .execute():🗄️ MÉTODO da biblioteca Supabase. Executa a consulta que acabamos de montar.
    response = (
        supabase
        .table("game")
        .select("*")
        .execute()
    )   #Pode ser escrita em uma linha só: response = supabase.table("game").select("*").execute()

    # response.data contém os registros retornados pelo Supabase.
    # "data" é um ATRIBUTO do objeto de resposta.
    return response.data