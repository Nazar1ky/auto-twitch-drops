from random import randrange

def create_nonce(length=30) -> str:
    nonce = ""
    for i in range(length):
        char_index = randrange(0, 10 + 26 + 26)
        if char_index < 10:
            char = chr(ord("0") + char_index)
        elif char_index < 10 + 26:
            char = chr(ord("a") + char_index - 10)
        else:
            char = chr(ord("A") + char_index - 26 - 10)
        nonce += char
    return nonce

def get_drop_image_id(drop_url):
    return drop_url.split("/")[5].split(".")[0]