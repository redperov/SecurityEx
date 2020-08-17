from flask import Flask, request, jsonify
from flask_caching import Cache
import requests
import sys
import os
import ast

from src.myEncryption.DiffieHellman import DiffieHellman

# config = {
#     "DEBUG": True,  # some Flask specific configs
#     "CACHE_TYPE": "simple",  # Flask-Caching related configs
#     "CACHE_DEFAULT_TIMEOUT": 300
# }
from src.onionComponents.onionUtils import decrypt_data, encrypt_data, generate_unique_id, send_request

"""
An implementation of a node.
Its purpose is to perform relay messages to other nodes/servers,
by decrypting and encrypting a single layer from the given onion.
"""

app = Flask(__name__)

# Routes between nodes
_shared_routes = {}

# Connection configurations
_connection = {}

# Directory node configurations
_directory_node = {}

# Diffie-Hellman protocol instance for key sharing
_diffie_hellman = DiffieHellman()


def main():
    if len(sys.argv) != 6:
        raise ValueError("Expected to receive server name, hostname, port and directory node hostname, port")
    current_name = sys.argv[1]
    current_hostname = sys.argv[2]
    current_port = sys.argv[3]
    directory_hostname = sys.argv[4]
    directory_port = sys.argv[5]

    # Save configurations.
    _connection["name"] = current_name
    _connection["hostname"] = current_hostname
    _connection["port"] = current_port
    _connection["publicKey"] = _diffie_hellman.get_public_key()
    _connection["salt"] = os.urandom(16).decode("ISO-8859-1")
    print(str.format("Received public key: {0}", _connection["publicKey"]))

    _directory_node["hostname"] = directory_hostname
    _directory_node["port"] = directory_port

    # Publish the node to the node directory
    publish_node()

    # Run the server
    app.run(host=current_hostname, port=current_port)


def publish_node():
    """
    Notify the directory node about the existence of the current node.
    """
    directory_node_uri = str.format("http://{0}:{1}/addNode",
                                    _directory_node["hostname"], _directory_node["port"])
    print(str.format("Publishing node {0} with public key: {1}", _connection["name"], _connection["publicKey"]))
    response = requests.post(directory_node_uri, json=_connection).json()

    # Check if the directory node accepted the current node
    if response["success"]:
        print("Node published successfully")
    else:
        print("Failed publishing node")
        exit(1)


@app.route("/keyShare", methods=["POST"])
def key_share():
    """
    Shares the public key of the current node with the sender and generates a shared key using the input key.
    """
    request_data = request.get_json()

    # Check if the key sharing request is valid
    if not _is_valid_key_sharing_request(request_data):
        return jsonify(success=False)
    message = request_data["message"]
    other_public_key = message["publicKey"]
    print(str.format("Received public key: {0}", other_public_key))
    source_uri = request_data["sourceUri"]

    # Create the shared key
    shared_key = _diffie_hellman.generate_shared_key(other_public_key, _connection["salt"].encode("ISO-8859-1"))

    # Create a new route between the request's source and the current node
    shared_route = {"source": source_uri,  # "keyId": key_id,
                    "sharedKey": shared_key}
    _shared_routes[source_uri] = shared_route
    print(str.format("Added shared key with {0}, value: {1}", source_uri, shared_key))

    return jsonify(success=True)


@app.route("/relay", methods=["POST"])
def accept_relay():
    """
    Performs a relay of the given request.
    """
    request_data = request.get_json()

    # Check if the given relay request is valid
    if not _is_valid_relay_request(request_data):
        return jsonify(success=False)
    response = _pass_message(request_data)

    return response


def _is_valid_key_sharing_request(request_data):
    """
    Checks if the given request is a valid key sharing request.
    :param request_data: request to check
    :return: is the request a valid key sharing request
    """
    return request_data and ("message" in request_data) and ("publicKey" in request_data["message"])


def _is_valid_relay_request(request_data):
    return request_data and ("message" in request_data)


def _pass_message(request_data):
    """
    Passes the given message to its next destination.
    :param request_data: request to pass
    """
    source_uri = request_data["sourceUri"]
    shared_route = _shared_routes[source_uri]
    key = shared_route["sharedKey"]
    encrypted_message = request_data["message"].encode("ISO-8859-1")

    # Decrypt a single layer from the given node using the established shared key
    decrypted_message_bytes = decrypt_data(encrypted_message, key)
    decrypted_message_json = ast.literal_eval(
        decrypted_message_bytes.decode('utf-8'))
    destination_uri = decrypted_message_json["nextDestination"]

    try:
        message = decrypted_message_json["message"].decode("ISO-8859-1")
    except (UnicodeDecodeError, AttributeError):
        message = decrypted_message_json["message"]
    connection_id = generate_unique_id()
    source_uri = str.format("{0}:{1}", _connection["hostname"], _connection["port"])
    message = {"message": message, "connectionId": connection_id, "sourceUri": source_uri}
    response = send_request(destination_uri, message)
    response_bytes = str(response).encode("ISO-8859-1")

    # Encrypt the response with a single layer
    _, encrypted_response_bytes = encrypt_data(response_bytes, key)
    encrypted_response_json = {"message": encrypted_response_bytes.decode("ISO-8859-1")}
    return encrypted_response_json


if __name__ == "__main__":
    main()
