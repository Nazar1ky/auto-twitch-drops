import requests
import logging
from .constants import CLIENT_ID
import os
import json
from time import sleep

class TwitchLogin:
    def login(self):
        save_cookies = False

        if not self.load_cookies():
            device_code = self.get_device_code()
            logging.info(f"Please login in: {device_code["verification_uri"]} | Expires in {device_code["expires_in"] / 60} minutes!")

            while True:
                try:
                    self.get_token(device_code["device_code"])
                except:
                    sleep(device_code["interval"])
                else:
                    break

            save_cookies = True

        if not self.validate():
            self.remove_cookies()
            return False

        if save_cookies:
            self.save_cookies()

        return True

    def get_device_code(self):
        payload = {
            "client_id": CLIENT_ID,
            "scopes": " ".join([ # https://dev.twitch.tv/docs/authentication/scopes/ can be removed
                "channel_read",
                "chat:read", 
                "user_blocks_edit",
                "user_blocks_read",
                "user_follows_edit",
                "user_read",
            ]),
        }

        r = requests.post("https://id.twitch.tv/oauth2/device", data=payload)

        r.raise_for_status()

        return r.json()

    def get_token(self, device_code):
        payload = {
            "client_id": CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }
        r = requests.post("https://id.twitch.tv/oauth2/token", payload)
  
        r.raise_for_status()

        data = r.json()

        self.access_token = data["access_token"]

        return True

    def validate(self):
        headers = {
                "Authorization": f"OAuth {self.access_token}",
        }

        r = requests.get("https://id.twitch.tv/oauth2/validate", headers=headers)

        if r.status_code != 200:
            return False

        data = r.json()

        self.nickname = data["login"].lower()
        self.user_id = data["user_id"]

        return True

    def save_cookies(self):
        cookies = {
            "access_token": self.access_token,
            "nickname": self.nickname,
            "user_id": self.user_id,
        }

        with open("cookies.json", "w", encoding="utf-8") as file:
            json.dump(cookies, file, ensure_ascii=False, indent=4)

    def load_cookies(self):
        try:
            with open("cookies.json", encoding="utf-8") as file:
                cookies = json.load(file)

            self.access_token = cookies["access_token"]
            self.nickname = cookies["nickname"]
            self.user_id = cookies["user_id"]

        except FileNotFoundError:
            return False
        else:
            return True

    def remove_cookies(self):
        if os.path.exists("cookies.json"):
            os.remove("cookies.json")