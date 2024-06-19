import asyncio
import json
import logging

import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from .constants import WEBSOCKET
from .utils import create_nonce


class TwitchWebSocket:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.websocket = None
        self.closed = False

        self.accounts_topics = []
        self.channels_updates = []


    async def connect(self):
        self.websocket = await websockets.connect(WEBSOCKET)
        self.logger.info("Connected to websocket")


    async def is_connected(self):
        return self.websocket is not None and self.websocket.open


    async def reconnect(self):
        self.logger.info("Reconnecting...")

        self.websocket = None

        while True:
            try:
                self.websocket = await websockets.connect(WEBSOCKET)
            except (ConnectionClosedError, ConnectionClosedOK):
                self.logger.exception("Error while reconnecting. Retry in 15 seconds.")
                asyncio.sleep(15)
            else:
                break

        if self.accounts_topics:
            for topic in self.accounts_topics:
                await self.listen_topics(topic["topics"], topic["login"])

        if self.channels_updates:
            for channel_update in self.channels_updates:
                await self.listen_topics([f"broadcast-settings-update.{channel_update["channel_id"]}"])

        self.logger.info("Reconnected. All topics listened")


    async def send_data(self, data):
        try:
            await self.websocket.send(json.dumps(data))
        except (ConnectionClosedError, ConnectionClosedOK):
            if self.closed:
                return

            self.logger.exception("Connection error")
            await self.reconnect()


    async def receive_messages(self):
        try:
            msg = await self.websocket.recv()
            self.logger.debug(f"Received message: {msg.strip()}")

            response = json.loads(msg)

            # RECONNECT
            if response["type"] == "RECONNECT":
                self.logger.warning("Websocket reconnecting...")
                await self.reconnect()

            # HANDLE MESSAGE
            elif response["type"] == "MESSAGE" and response["data"].get("message"):
                message_type, id_ = response["data"]["topic"].split(".")
                message = json.loads(response["data"]["message"])

                await self.handle_message(message, message_type, id_)

        except (ConnectionClosedError, ConnectionClosedOK):
            if self.closed:
                return

            self.logger.exception("Connection error")
            await self.reconnect()


    async def close(self):
        self.closed = True

        await self.websocket.close()
        self.logger.info("WebSocket connection closed")


    # TASKS
    async def run_ping(self):
        while not self.closed:
            if not await self.is_connected():
                await asyncio.sleep(5)
                continue

            await self.send_ping()
            await asyncio.sleep(60)

    async def run_message_handler(self):
        while not self.closed:
            if not await self.is_connected():
                await asyncio.sleep(5)
                continue

            await self.receive_messages()


    # EXTRA FUNCTIONS
    async def send_ping(self):
        data = { "type": "PING" }
        await self.send_data(data)

        self.logger.debug("Ping sent")


    async def handle_message(self, message, message_type, id_):
            # HANDLE GAME CHANGE
            if message_type == "broadcast-settings-update":  # noqa: SIM102
                if message["type"] == "broadcast_settings_update":
                    channel, i = await self.find_channel_updates(id_)
                    channel["game_id"] = message["game_id"]

            # HANDLE DROP MINED NOTIFICATION
            if message_type == "onsite-notifications":  # noqa: SIM102
                if message["type"] == "create-notification":
                    message_data = message["data"]["notification"]
                    if message_data["type"] == "user_drop_reward_reminder_notification":
                        account = await self.find_account(id_)
                        account["drop_mined"] = True


    async def find_account(self, user_id):
        for account in self.accounts_topics:
            if account["login"].user_id != user_id:
                continue

            return account

        return None


    async def find_channel_updates(self, channel_id):
        for i, channel in enumerate(self.channels_updates):
            if channel["channel_id"] != channel_id:
                continue

            return channel, i

        raise RuntimeError("Not founded")


    async def listen_channel_updates(self, channel_id, login):
        try:
            channel, i = await self.find_channel_updates(channel_id)
            channel["uses"].append(login.user_id)
        except RuntimeError:
            topic = [f"broadcast-settings-update.{channel_id}"]
            await self.listen_topics(topic)

            self.channels_updates.append({
                "channel_id": channel_id,
                "game_id": None,
                "uses": [login.user_id],
            })

            self.logger.debug(f"channels_updates updated: {self.channels_updates}")


    async def unlisten_channel_updates(self, channel_id, login):
        channel, i = await self.find_channel_updates(channel_id)

        if len(channel["uses"]) >= 2:
            channel["uses"].remove(login.user_id)
            return

        topic = [f"broadcast-settings-update.{channel_id}"]
        await self.unlisten_topics(topic)

        del self.channels_updates[i]

        self.logger.debug(f"channels_updates updated (remove): {self.channels_updates}")

    async def add_topics(self, login, topics):
        await self.listen_topics(topics, login)
        self.accounts_topics.append({
            "topics": topics,
            "drop_mined": False,
            "login": login,
        })

        self.logger.debug(f"accounts_topics updated: {self.accounts_topics}")


    async def listen_topics(self, topics, login=None):
        data = {
            "data": {
                "topics": topics,
            },
            "nonce": create_nonce(),
            "type":"LISTEN",
        }
        if login: data["data"]["auth_token"] = login.access_token

        await self.send_data(data)
        self.logger.debug(f"Listen topics: {topics}")


    async def unlisten_topics(self, topics, login=None):
        data = {
            "data": {
                "topics": topics,
            },
            "nonce": create_nonce(),
            "type":"UNLISTEN",
        }
        if login: data["data"]["auth_token"] = login.access_token

        await self.send_data(data)
        self.logger.debug(f"Unlisten topics: {topics}")
