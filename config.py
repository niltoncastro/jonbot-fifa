import os

# configuração das ligas/torneios
TOURNAMENT_CONFIG = {
    "2361937986599399439": {
        "name": "Venezuela",
        "url": "https://jonbet.bet.br/pt/sports?bt-path=%2Fesoccer%2Fvenezuela%2Fliga-futve-2x6-min-2361937986599399439",
        "stats": True
    }
}

env_type = os.getenv("ENV_TYPE", "local")  # default = local

if env_type == "server":
    from config_server import paths
else:
    from config_local import paths
