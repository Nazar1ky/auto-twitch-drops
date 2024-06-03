import logging

from autoTwitchDrops.TwitchLogin import TwitchLogin
from autoTwitchDrops.TwitchMine import TwitchMine

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter("{asctime} | {levelname} | {funcName:<24s} | {message}", style="{", datefmt="%H:%M:%S")

file_handler = logging.FileHandler("log.log", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

logging.getLogger("chardet.charsetprober").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("websocket").setLevel(logging.ERROR)

if __name__ == "__main__":
    login = TwitchLogin()

    if login.login():
        logging.info(f"Successfully logged in as {login.nickname}")

    app = TwitchMine(login)
    app.start()
    # while True:
    #     app.send_watch("valorant")
    #     # app.send_watch("redbeard")
    #     time.sleep(14)
#15 42

""" TODO:
Refactor
Unittests(?)
AIOHTTP


Smart Load:
* Load all streamers that stream that game
* Find last drop or more mined drop and mine it

more functions find_channel_to_watch

refactor everything

module logging queue required
"""
