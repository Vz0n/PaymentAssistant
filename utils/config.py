from tomlkit import load, dump
from os import urandom, environ
from flask import Flask

CONFIG_FILENAME = "config.toml"
DEFAULT = f"""[main]
# The canonical url that the app will use for links and access
app_url = "http://127.0.0.1:8000"
# Bind address
bind = "127.0.0.1:8000"
# Key used for signing cookies. Changing this will cause users to get logged out
secret_key = "{urandom(24).hex()}"
# Server debug mode. Don't enable it in production.
debug = false
# Fee payment dates
fee_dates = ["2025-01-20", "2025-02-20", "2025-04-20", "2025-05-20", "2025-06-20"]
# Fees price
fee_price = "96"
"""

class Config:
    def __init__(self):
        try:
            self.__load_document__()
        except FileNotFoundError:
            handle = open(CONFIG_FILENAME, "w")
            handle.write(DEFAULT)
            handle.close()

            self.__load_document__()
    
    def __load_document__(self):
        file = open(CONFIG_FILENAME, "r")
        self.document = load(file)
        file.close()

    def get(self, key: str):
        return self.document.get("main")[key]
    
    def set(self, key: str, value: any):
        self.document.get("main")[key] = value

    def save(self):
        file = open(CONFIG_FILENAME, "w")
        dump(self.document, file)
        file.close()

def set_app_config(cfg: Config, app: Flask):
    app.__setattr__("assistant_config", cfg)
    app_url = cfg.get("app_url").split("://")

    app.config["SECRET_KEY"] = cfg.get("secret_key")
    app.config["SESSION_COOKIE_NAME"] = "passis_user"
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PREFERRED_URL_SCHEME"] = app_url[0]
    app.config["SERVER_NAME"] = app_url[1]
    app.config["FROM_EMAIL"] = environ["SMTP_FROM_ADDRESS"]
    app.config["MAX_FORM_PARTS"] = 20