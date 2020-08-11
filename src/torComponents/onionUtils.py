import requests
import uuid

import src.myEncryption.DES as my_encryption


def encrypt_data(data, encryption_key):
    """
    Encrypts the given data using DES.
    :param data: data to encrypt
    :param encryption_key: encryption key to use while encrypting
    :return: encryption algorithm, encrypted data
    """
    des = my_encryption.DES(encryption_key, b"\0\0\0\0\0\0\0\0", pad=b"$")
    encrypted_data = des.encrypt(data)
    print("Encrypted: %r" % encrypted_data)

    return des, encrypted_data


# TODO if the shared key not needed, remove it from the places that don't use it,
# TODO or modify the algorithm to accept it as input
def decrypt_data(encrypted_data, decryption_key):
    des = my_encryption.DES(decryption_key, b"\0\0\0\0\0\0\0\0", pad=b"$")
    decrypted_data = des.decrypt(encrypted_data)
    print("Decrypted: %r" % decrypted_data)

    return decrypted_data


def generate_unique_id():
    return uuid.uuid4()


def send_request(destination_uri, message):
    response = requests.post(destination_uri, json=message).json()
    return response
