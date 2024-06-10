import string
from random import sample


def create_nonce(length=30) -> str:
    return "".join(sample(string.digits + string.ascii_letters, length))

def sort_campaigns(data):
    return sorted(data, key=lambda x: (
        -x.channelsEnabled,
        x.game["displayName"],
        x.endAt))
