import logging

from src.TwitchLogin import TwitchLogin
from src.TwitchMine import TwitchMine
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('{asctime} | {levelname} | {funcName:<17s} | {message}', style='{', datefmt="%H:%M:%S")

file_handler = logging.FileHandler("log.log", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)


if __name__ == "__main__":
    login = TwitchLogin()

    if login.login():
        logging.info(f"Successfully logged in as {login.nickname}")

    app = TwitchMine(login)
    app.start()
    # while True:
    #     app.send_watch("tracknumberseven")
    #     # app.send_watch("redbeard")
    #     time.sleep(14)
#15 42

""" TODO:
Every class - different file
Refactor
Unittests(?)
TEST Signature and value
AIOHTTP


Smart Load:
* Load all streamers that stream that game
* Find last drop or more mined drop and mine it
"""