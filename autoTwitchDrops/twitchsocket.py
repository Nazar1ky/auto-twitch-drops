import asyncio
import json
import logging

import websockets

from .constants import WEBSOCKET
from .utils import create_nonce


class TwitchWebSocket:
    logger = logging.getLogger(__name__)

    def __init__(self, login, topics):
        self.login = login
        self.current_channel = None
        self.topics = topics
        self.url = WEBSOCKET
        self.websocket = None

    async def run_ping(self):
        while True:
            try:
                await self.send_ping()
                await asyncio.sleep(60)
            except Exception:
                self.logger.exception("Websocket error, reconnect.")
                self.websocket.connect()

    async def connect(self):
        await self.close()

        self.websocket = await websockets.connect(self.url)
        await self.listen_topics(self.topics)
        if self.current_channel: await self.switch_channel_topic(self.current_channel)

        self.logger.info("Connected to websocket")

    async def switch_channel_topic(self, channel_id = None):
        if channel_id is None:
            return

        if self.current_channel and self.current_channel != channel_id:
            topic = [{"text": "broadcast-settings-update.CHANNEL_ID", "channel_id": self.current_channel}]
            await self.unlisten_topics(topic)

        self.current_channel = channel_id
        topic = [{"text": "broadcast-settings-update.CHANNEL_ID", "channel_id": self.current_channel}]
        await self.listen_topics(topic)

    async def listen_topics(self, topics):
        topics = [topic["text"].replace("USER_ID", self.login.user_id).replace("CHANNEL_ID", topic["channel_id"] if topic.get("channel_id") else "") for topic in topics]

        data = {
            "data": {
                "auth_token": self.login.access_token,
                "topics": topics,
            },
            "nonce": create_nonce(),
            "type":"LISTEN",
        }

        await self.websocket.send(json.dumps(data))
        self.logger.debug(f"Listen topics: {topics}")

    async def unlisten_topics(self, topics):
        topics = [topic["text"].replace("USER_ID", self.login.user_id).replace("CHANNEL_ID", topic["CHANNEL_ID"]) for topic in topics]

        data = {
            "data": {
                "auth_token": self.login.access_token,
                "topics": topics,
            },
            "nonce": create_nonce(),
            "type":"UNLISTEN",
        }

        await self.websocket.send(json.dumps(data))
        self.logger.debug(f"Unlisten topics: {topics}")

    async def send_ping(self):
        data = {"type":"PING"}
        await self.websocket.send(json.dumps(data))
        self.logger.info("Server pinged")


    async def receive_message(self):
            async for message in self.websocket:
                self.logger.debug(f"Received message: {message.strip()}")

                response = json.loads(message)

                if response["type"] == "RECONNECT":
                    self.logger.warning("Websocket reconnecting...")
                    await self.reconnect()

                if response["type"] == "MESSAGE":
                    return response["data"]

            return None

    async def close(self):
        if self.websocket:
            await self.websocket.close()
            self.logger.info("WebSocket connection closed")
