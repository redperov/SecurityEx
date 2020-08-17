from flask import Flask, request, jsonify
import requests
import sys
import random
import ast

from src.myEncryption.DiffieHellman import DiffieHellman
from src.onionComponents.onionUtils import encrypt_data, decrypt_data, send_request, generate_unique_id

"""
An implementation of an onion proxy.
Its purpose is to receive a request from a user and to send it to its destination in an anonymous way,
using an onion routing protocol.
"""

app = Flask(__name__)

# Connection configurations
_connection = {}

# Directory node configurations
_directory_node = {}

# Constants
NUM_OF_NODES_IN_PATH = 3
MINIMUM_NODES_IN_PATH = 3


def main():
    if len(sys.argv) != 5:
        raise ValueError("Expected to receive server hostname, port and directory node hostname, port")
    current_hostname = sys.argv[1]
    current_port = sys.argv[2]
    directory_hostname = sys.argv[3]
    directory_port = sys.argv[4]

    # Save the configurations
    _connection["hostname"] = current_hostname
    _connection["port"] = current_port
    _directory_node["hostname"] = directory_hostname
    _directory_node["port"] = directory_port

    # Run the server
    app.run(host=current_hostname, port=current_port)


@app.route("/", methods=["GET"])
def hide_request():
    """
    Encrypts the given request in multiple layers of encryption and sends the resulted onion throughout the system.
    """
    args = request.args

    # Check if the request is valid
    if not _is_valid_args(args):
        return jsonify(success=False)
    destination_uri = args["req"]
    destination_message = args["msg"]

    # Choose a path of nodes through which the message will be sent
    path = _choose_path(NUM_OF_NODES_IN_PATH)

    # Create shared keys between the chosen nodes
    _create_shared_keys(path)

    # Encrypt the message in multiple layers
    onion_message = _create_onion(path, destination_uri, destination_message)

    # Send the encrypted message through the path
    onion_response = _send_hidden_request(onion_message)

    # Decrypt the response
    response = decrypt_response(onion_response, path)
    return response


def _is_valid_args(args):
    """
    Checks if the given arguments are valid.
    :param args: arguments to check
    :return: are the arguments valid
    """
    return args and "req" in args and "msg" in args


def _choose_path(path_length):
    """
    Chooses a path on nodes.
    :param path_length: desired path length
    :return:
    """
    directory_node_uri = str.format("http://{0}:{1}/getAllNodes",
                                    _directory_node["hostname"], _directory_node["port"])
    response = requests.get(directory_node_uri).json()
    nodes = response["nodes"]

    # Validate the path length
    if len(nodes) < path_length:
        raise ValueError("Path size is larger than the number of available nodes")
    if len(nodes) < MINIMUM_NODES_IN_PATH:
        raise ValueError(str.format("The path must consist of at least {0} nodes", MINIMUM_NODES_IN_PATH))
    chosen_path = []

    # Choose random nodes from all the available nodes
    for i in range(path_length):
        chosen_node = random.choice(nodes)
        chosen_path.append(chosen_node)
        nodes.remove(chosen_node)
    print(str.format("Chosen path: {0}", chosen_path))

    return chosen_path


def _create_shared_keys(nodes):
    """
    Creates shared keys between the current server and the given nodes.
    :param nodes: nodes to share keys with
    """
    print("Performing key sharing...")
    nodes_before_key_exhange = []

    for node in nodes:
        diffie_hellman = DiffieHellman()
        source_public_key = diffie_hellman.get_public_key()
        print(str.format("Generated public key: {0}", source_public_key))
        other_public_key = node["publicKey"]
        other_salt = node["salt"].encode("ISO-8859-1")
        print(str.format("Other public key: {0}", other_public_key))
        shared_key = diffie_hellman.generate_shared_key(other_public_key, other_salt)
        print(str.format("Created shared key with {0}, value: {1}", node["name"], shared_key))

        # Send the current server's public key to the other node
        _send_public_key(source_public_key, nodes_before_key_exhange, node)

        # Save the shared key
        node["sharedKey"] = shared_key
        nodes_before_key_exhange.append(node)
    print("Finished key sharing")

    return nodes


def _send_public_key(source_public_key, nodes_before_key_exchange, destination_node):
    """
    Sends the given public key to the desired node
    :param source_public_key: public key to send
    :param nodes_before_key_exchange: nodes preceding the desired destination node
    :param destination_node: destination node to send public key to
    """
    node_uri = str.format("http://{0}:{1}/keyShare", destination_node["hostname"], destination_node["port"])
    message = {"publicKey": source_public_key}
    onion = _create_onion(nodes_before_key_exchange, node_uri, message)
    onion_response = _send_hidden_request(onion)
    decrypted_response = decrypt_response(onion_response, nodes_before_key_exchange)

    # Check if the key was sent successfully
    if "success" in decrypted_response and decrypted_response["success"]:
        print(str.format("Successfully send public key to {0}", destination_node["name"]))
    else:
        print(str.format("Failed sending public key to {0}", destination_node["name"]))


def _create_onion(path, final_destination, message):
    """
    Encrypt the given message with multiple layers of encryption.
    :param path: path thorough which the encrypted message will be sent
    :param final_destination: the destination of the encrypted message
    :param message: message to send
    """
    current_onion = {"message": message, "nextDestination": final_destination}

    for i in range(len(path)):
        next_node = path[-(i + 1)]
        next_destination = str.format("http://{0}:{1}/relay", next_node["hostname"], next_node["port"])
        shared_key = next_node["sharedKey"]
        current_onion_bytes = str(current_onion).encode("ISO-8859-1") 
        layer_algorithm, encrypted_layer = encrypt_data(current_onion_bytes, shared_key)
        next_node["encryptionAlgorithm"] = layer_algorithm
        current_onion = {"message": encrypted_layer, "nextDestination": next_destination}

    return current_onion


def _send_hidden_request(onion_message):
    """
    Sends the given encrypted message to the first node in the path
    :param onion_message:
    :return:
    """
    try:
        message = onion_message["message"].decode("ISO-8859-1")
    except (UnicodeDecodeError, AttributeError):
        message = onion_message["message"]
    destination_uri = onion_message["nextDestination"]
    connection_id = generate_unique_id()
    source_uri = str.format("{0}:{1}", _connection["hostname"], _connection["port"])
    message = {"message": message, "connectionId": connection_id, "sourceUri": source_uri}
    response = send_request(destination_uri, message)

    return response


def decrypt_response(onion_response, path):
    """
    Decrypts the given response
    :param onion_response: response to decrypt
    :param path: path through which the respond traveled
    """
    current_onion = onion_response

    for node in path:
        shared_key = node["sharedKey"]
        encrypted_message = current_onion["message"]
        encrypted_message_bytes = str(encrypted_message).encode("ISO-8859-1")  # TODO change to iso?
        decrypted_message_bytes = decrypt_data(encrypted_message_bytes, shared_key)
        current_onion = ast.literal_eval(decrypted_message_bytes.decode('ISO-8859-1'))

    return current_onion


if __name__ == "__main__":
    main()
