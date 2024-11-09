import hashlib


def generate_hash(text: str) -> str:
    if isinstance(text, list):
        text = ''.join(text)
    text_bytes = text.encode('utf-8')
    sha256_hash = hashlib.sha256(text_bytes).hexdigest()
    return sha256_hash
