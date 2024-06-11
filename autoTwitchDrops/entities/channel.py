class Channel:
    def __init__(self, data):
        self.id = data["id"]

        if data.get("broadcaster"):
            self.nickname = data["broadcaster"]["login"]
        else:
            self.nickname = data["login"]
        if data.get("broadcastSettings"):
            self.game = data["broadcastSettings"]["game"]
        else:
            self.game = data["game"]
