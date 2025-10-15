import os

env_type = os.getenv("ENV_TYPE", "local")  # default = local

if env_type == "server":
    from config_server import paths
else:
    from config_local import paths
