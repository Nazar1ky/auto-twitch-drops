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
        self.topics = topics

        self.websocket = None

        self.current_channel_id = None

    async def run_ping(self):
        while True:
            if await self.is_connected():
                await self.send_ping()
                await asyncio.sleep(60)
            else:
                await self.connect()

    async def connect(self):
        await self.close()

        self.websocket = await websockets.connect(WEBSOCKET)
        await self.listen_topics(self.topics)
        await self.listen_channel_updates(self.current_channel_id)

        self.logger.info("Connected to websocket")

    async def is_connected(self):
        return self.websocket is not None and self.websocket.open

    async def listen_channel_updates(self, channel_id):
        if not channel_id:
            return

        if self.current_channel_id != channel_id:
            await self.unlisten_channel_updates()

        self.current_channel_id = channel_id
        topic = [f"broadcast-settings-update.{self.current_channel_id}"]
        await self.listen_topics(topic)

    async def unlisten_channel_updates(self):
        if not self.current_channel_id:
            return

        topic = [f"broadcast-settings-update.{self.current_channel_id}"]
        await self.unlisten_topics(topic)
        self.current_channel_id = None

    async def listen_topics(self, topics):
        data = {
            "data": {
                "auth_token": self.login.access_token,
                "topics": topics,
            },
            "nonce": create_nonce(),
            "type":"LISTEN",
        }

        await self.send_data(data)
        self.logger.debug(f"Listen topics: {topics}")

    async def unlisten_topics(self, topics):
        data = {
            "data": {
                # "auth_token": self.login.access_token,
                "topics": topics,
            },
            "nonce": create_nonce(),
            "type":"UNLISTEN",
        }

        await self.send_data(data)
        self.logger.debug(f"Unlisten topics: {topics}")

    async def send_data(self, data):
        if await self.is_connected():
            await self.websocket.send(json.dumps(data))
        else:
            await self.connect()

    async def send_ping(self):
        data = {"type":"PING"}
        await self.send_data(data)
        self.logger.debug("Server pinged")


    async def receive_message(self):
            if await self.is_connected():
                msg = await self.websocket.recv()
                self.logger.debug(f"Received message: {msg.strip()}")

                response = json.loads(msg)

                if response["type"] == "RECONNECT":
                    self.logger.warning("Websocket reconnecting...")
                    await self.connect()

                if response["type"] == "MESSAGE":
                    return response["data"]
            else:
                await self.connect()

            return None

    async def close(self):
        if await self.is_connected():
            await self.websocket.close()
            self.logger.info("WebSocket connection closed!")
