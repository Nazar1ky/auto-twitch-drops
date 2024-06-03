import string
from random import sample


def create_nonce(length=30) -> str:
    return "".join(sample(string.digits + string.ascii_letters, length))

def get_drop_image_id(drop_url):
    return drop_url.split("/")[5].split(".")[0]