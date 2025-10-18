def paths(parameter):
    mapping = {
        "db_path": "/home/jonbot/jonbot-fifa/database/jonbet-bot",
        "fire_fox": "/usr/bin/firefox",  # ou o caminho real encontrado
    }
    return mapping.get(parameter, parameter)
