
def paths(parameter):
    mapping = {
        "db_path": "C:/Users/junio/Desktop/workspace/database/jonbet-bot-db/jonbet-bot",
        "fire_fox": "C:/Program Files/Mozilla Firefox/firefox.exe",
    }
    return mapping.get(parameter, parameter)
