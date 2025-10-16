def paths(parameter):
    mapping = {
        "db_path": "/home/jonbot/jonbot-fifa/database/jonbet-bot.db",
        "fire_fox": "/snap/firefox/current/usr/lib/firefox/firefox",
    }
    return mapping.get(parameter, parameter)
