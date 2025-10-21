import os
from datetime import datetime, timedelta

# configuração das ligas/torneios
TOURNAMENT_CONFIG = {
    "2361937986599399439": {
        "name": "Venezuela",
        "url": "https://jonbet.bet.br/pt/sports?bt-path=%2Fesoccer%2Fvenezuela%2Fliga-futve-2x6-min-2361937986599399439",
        "stats": True
    }
}

env_type = os.getenv("ENV_TYPE", "local")  # default = local

# noinspection PyUnusedImports
if env_type == "server":
    from config_server import paths

    def data_hora_format():
        data_hora = datetime.now() - timedelta(hours=5)
        return data_hora.strftime('%Y-%m-%d %H:%M:%S')

else:
    from config_local import paths

    def data_hora_format():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
