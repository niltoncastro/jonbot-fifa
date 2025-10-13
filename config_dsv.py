def paths(parameter):
    mapping = {
        "db_path": "C:/Users/junio/Desktop/workspace/database/jonbet-bot-db/jonbet-bot",
        "fire_fox": "C:/Program Files/Mozilla Firefox/firefox.exe",
        "file_server_local": "C:\\Users\\junio\\Desktop\\workspace\\python\\jonbot\\files\\",
        "insert_resultado": "C:\\Users\\junio\\Desktop\\workspace\\sqls\\"
    }
    return mapping.get(parameter, parameter)
