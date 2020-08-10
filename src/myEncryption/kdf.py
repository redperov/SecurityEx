import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

backend = default_backend()
salt = os.urandom(16)
info = b"hkdf-usage"
KEY_SIZE = 8


def perform_kdf(input_key):
    """
    Perform key derivation on the given key to transform it to the desired length.
    Uses HKDF.
    :param input_key: key to transform (in bytes)
    :param desired_length: desired output key length
    :return: derived key
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        info=info,
        backend=backend)
    derived_key = hkdf.derive(input_key)

    return derived_key
