# Importa a função responsável por carregar as variáveis do arquivo .env
# Tanto .env quanto dotenv vem da palavra environment.
# FUNÇÃO EXTERNA: instalada na .venv através do pacote python-dotenv.
from dotenv import load_dotenv

# Importa o módulo da biblioteca padrão do Python para acessar variáveis de ambiente
import os

from supabase import create_client

# Carrega as variáveis definidas no arquivo .env
load_dotenv()

# Busca as variáveis de ambiente (URL carregada) do .env e guarda seus valores em variáveis Python
# O nome "SUPABASE_URL" está com aspas porque é uma string, então o Python entende que
# é o nome da variável de ambiente que queremos acessar, ou seja, https://ikmadcldfxvnupajxdwm.supabase.co.
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 🧑‍💻 VARIÁVEL NOSSA: supabase.
# create_client() é uma FUNÇÃO do pacote Supabase.
# Ela recebe nossa URL e nossa chave e retorna um objeto cliente do Supabase.
# Esse objeto será usado pelo backend para realizar operações no Supabase.
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
