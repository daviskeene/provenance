# crypto.py
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
import base64
import os
from dotenv import load_dotenv

load_dotenv()


def load_private_key(path=os.getenv("PRIVATE_KEY_PATH")):
    with open(path, "rb") as f:
        key_data = f.read()
    # Use load_pem_private_key to parse the PEM
    private_key = serialization.load_pem_private_key(
        key_data,
        password=None,
    )
    # private_key is now an Ed25519PrivateKey instance
    return private_key


def load_public_key(path=os.getenv("PUBLIC_KEY_PATH")):
    with open(path, "rb") as f:
        key_data = f.read()
    public_key = serialization.load_pem_public_key(key_data)
    return public_key


def sign_data(private_key: Ed25519PrivateKey, data: bytes) -> str:
    signature = private_key.sign(data)
    return base64.b64encode(signature).decode("utf-8")


def verify_signature(
    public_key: Ed25519PublicKey, data: bytes, signature_str: str
) -> bool:
    signature = base64.b64decode(signature_str)
    try:
        public_key.verify(signature, data)
        return True
    except Exception:
        return False


def hash_data(data: str) -> bytes:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data.encode("utf-8"))
    return digest.finalize()
