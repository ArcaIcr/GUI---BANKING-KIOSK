# security.py
import os
import hashlib

ITERATIONS = 100_000

def hash_pin(pin: str):
    salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        salt,
        ITERATIONS
    )
    # store salt + hash together
    return salt + hash_bytes


def verify_pin(pin: str, stored_hex: str) -> bool:
    data = bytes.fromhex(stored_hex)
    salt = data[:16]
    stored_hash = data[16:]

    new_hash = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        salt,
        ITERATIONS
    )
    return new_hash == stored_hash
