import requests
import uuid

import src.myEncryption.DES as my_encryption

"""
Utilities which are used in the system.
"""


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

def decrypt_data(encrypted_data, decryption_key):
    """
    Decrypts data using a shared key.
    :param encrypted_data: data to decrypt
    :param decryption_key: decryption key
    :return: decrypted data
    """
    des = my_encryption.DES(decryption_key, b"\0\0\0\0\0\0\0\0", pad=b"$")
    decrypted_data = des.decrypt(encrypted_data)
    print("Decrypted: %r" % decrypted_data)

    return decrypted_data


def generate_unique_id():
    """
    Generates a unique id.
    :return: unique id
    """
    return str(uuid.uuid4())


def send_request(destination_uri, message):
    """
    Sends the given message using an HTTP Post request.
    :param destination_uri: destination to send the request to
    :param message: message to send
    :return: returned response
    """
    response = requests.post(destination_uri, json=message).json()
    return response
