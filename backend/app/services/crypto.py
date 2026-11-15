import base64
import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

class CryptoService:
    def __init__(self, key_str: str = settings.ENCRYPTION_KEY):
        if len(key_str) == 64:
            try:
                self.key = bytes.fromhex(key_str)
            except ValueError:
                self.key = hashlib.sha256(key_str.encode("utf-8")).digest()
        elif len(key_str) == 32:
            self.key = key_str.encode("utf-8")
        else:
            self.key = hashlib.sha256(key_str.encode("utf-8")).digest()
        self.aesgcm = AESGCM(self.key)

    def encrypt(self, plaintext: str) -> str:
        if plaintext is None:
            return ""
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt(self, encrypted_str: str) -> str:
        if not encrypted_str:
            return ""
        try:
            raw_data = base64.b64decode(encrypted_str.encode("utf-8"))
            nonce = raw_data[:12]
            ciphertext = raw_data[12:]
            return self.aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception:
            return encrypted_str

crypto_service = CryptoService()
