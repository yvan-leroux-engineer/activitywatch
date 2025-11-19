from aw_core.config import load_config_toml

default_config = """
[server]
hostname = "127.0.0.1"
port = "5600"
protocol = "http"
api_key = ""
verify_ssl = true

[client]
commit_interval = 10

[server-testing]
hostname = "127.0.0.1"
port = "5600"
protocol = "http"
api_key = ""
verify_ssl = true

[client-testing]
commit_interval = 5
""".strip()


def load_config():
    return load_config_toml("aw-client", default_config)
