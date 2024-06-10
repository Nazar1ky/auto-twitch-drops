import json
import logging

import websockets

from .constants import WEBSOCKET
from .utils import create_nonce


class TwitchWebSocket:
    logger = logging.getLogger(__name__)

    def __init__(self, login):
        self.login = login
        self.url = WEBSOCKET
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.url)
        self.logger.info("Connected to websocket")


    async def send_topics(self, topics):
        data = {
            "data": {
                "auth_token": self.login.access_token,
                "topics": [f"{topic["text"]}.{topic["channel_id"]}" if topic.get("channel_id") else f"{topic["text"]}.{self.login.user_id}" for topic in topics],
            },
            "nonce": create_nonce(),
            "type":"LISTEN",
        }

        await self.websocket.send(json.dumps(data))

    async def send_ping(self):
        data = {"type":"PING"}
        await self.websocket.send(json.dumps(data))
        self.logger.info("Server pinged")


    async def receive_message(self):
        async for message in self.websocket:
            self.logger.debug(f"Received message: {message.strip()}")

            response = json.loads(message)

            if response["type"] != "MESSAGE":
                return None

            return response["data"]
        return None

    async def close(self):
        if self.websocket:
            await self.websocket.close()
            self.logger.info("WebSocket connection closed")

# class TwitchWebSocketApp(WebSocketApp):
#     def __init__(self, twitch, *args, **kw):
#         super().__init__(*args, **kw)
#         self.twitch = twitch
#         self.is_opened = False

#     def listen(self, topic):
#         data = {"topics": [str(topic)]}
#         data["auth_token"] = self.twitch.login.access_token
#         nonce = create_nonce()
#         self.send({"type": "LISTEN", "nonce": nonce, "data": data})


#     def send(self, request):
#         request_str = json.dumps(request, separators=(",", ":"))
#         super().send(request_str)

#     def ping(self):
#         self.send({"type": "PING"})

# class TwitchWebSocket:
#     def __init__(self, twitch):
#         self.twitch = twitch

#     def run(self):
#         self.ws = TwitchWebSocketApp(
#             self.twitch,
#             url=WEBSOCKET,
#             on_message=self.on_message,
#             on_open=self.on_open,
#             on_error=self.on_error,
#             on_close=self.on_close,
#         )
#         t = threading.Thread(target=self.ws.run_forever)
#         t.daemon = True
#         t.start()

#     def close(self):
#         self.ws.close()

#     @staticmethod
#     def on_open(ws):
#         ws.listen(f"onsite-notifications.{ws.twitch.login.user_id}")

#         def run_ping():
#             while True:
#                 ws.ping()
#                 time.sleep(30)

#         t = threading.Thread(target=run_ping)
#         t.daemon = True
#         t.start()

#     @staticmethod
#     def on_close(ws, close_status_code, close_ms):
#         pass

#     @staticmethod
#     def on_message(ws, message):
#         response = json.loads(message)

#         if response["type"] != "MESSAGE":
#             return

#         message = response["data"]

#         topic, stopic_user = message["topic"].split(".")

#         if topic != "onsite-notifications":
#             return

#         message = json.loads(message["message"])["data"]

#         if not message.get("notification"):
#             return

#         notification = message["notification"]

#         image_url = get_drop_image_id(notification["thumbnail_url"])

#         ws.twitch.can_be_claimed.append(image_url)

#     @staticmethod
#     def on_error(ws, error):
#         pass
