from flask import Flask, request, jsonify
import requests
import sys
import random
import ast

from src.myEncryption.DiffieHellman import DiffieHellman
from src.torComponents.onionUtils import encrypt_data, decrypt_data, send_request, generate_unique_id

app = Flask(__name__)
_connection = {}
_directory_node = {}
NUM_OF_NODES_IN_PATH = 3
MINIMUM_NODES_IN_PATH = 3


def main():
    if len(sys.argv) != 5:
        raise ValueError("Expected to receive server hostname, port and directory node hostname, port")
    current_hostname = sys.argv[1]
    current_port = sys.argv[2]
    directory_hostname = sys.argv[3]
    directory_port = sys.argv[4]

    # # Save the connection parameters
    # cache.set("connection", {"name": current_name, "hostname": current_hostname, "port": current_port})
    # cache.set("directory_node", {"hostname": directory_hostname, "port": directory_port})

    _connection["hostname"] = current_hostname
    _connection["port"] = current_port
    _directory_node["hostname"] = directory_hostname
    _directory_node["port"] = directory_port

    # Run the server
    app.run(host=current_hostname, port=current_port)


@app.route("/", methods=["GET"])
def hide_request():
    args = request.args
    if not _is_valid_args(args):
        return jsonify(success=False)
    destination_uri = args["req"]
    destination_message = args["msg"]
    path = _choose_path(NUM_OF_NODES_IN_PATH)
    _create_shared_keys(path)
    onion_message = _create_onion(path, destination_uri, destination_message)  # TODO change that to user argument
    onion_response = _send_hidden_request(onion_message)
    response = decrypt_response(onion_response, path)
    return response


def _is_valid_args(args):
    return args and "req" in args and "msg" in args


def _choose_path(path_length):
    directory_node_uri = str.format("http://{0}:{1}/getAllNodes",
                                    _directory_node["hostname"], _directory_node["port"])
    # TODO validate the response
    response = requests.get(directory_node_uri).json()
    nodes = response["nodes"]

    if len(nodes) < path_length:
        raise ValueError("Path size is larger than the number of available nodes")
    if len(nodes) < MINIMUM_NODES_IN_PATH:
        raise ValueError(str.format("The path must consist of at least {0} nodes", MINIMUM_NODES_IN_PATH))
    chosen_path = []

    for i in range(path_length):
        chosen_node = random.choice(nodes)
        chosen_path.append(chosen_node)
        nodes.remove(chosen_node)
    print(str.format("Chosen path: {0}", chosen_path))

    return chosen_path


def _create_shared_keys(nodes):
    print("Performing key sharing...")
    nodes_before_key_exhange = []

    for node in nodes:
        # TODO maybe exchange the prime and modulus in the beginning to make it look real?
        diffie_hellman = DiffieHellman()
        source_public_key = diffie_hellman.get_public_key()
        print(str.format("Generated public key: {0}", source_public_key))
        other_public_key = node["publicKey"]
        other_salt = node["salt"].encode("ISO-8859-1")
        print(str.format("Other public key: {0}", other_public_key))
        shared_key = diffie_hellman.generate_shared_key(other_public_key, other_salt)
        print(str.format("Created shared key with {0}, value: {1}", node["name"], shared_key))

        _send_public_key(source_public_key, nodes_before_key_exhange, node)
        # node["encryptionAlgorithm"] = encryption_algorithm
        node["sharedKey"] = shared_key
        nodes_before_key_exhange.append(node)
    print("Finished key sharing")

    return nodes


def _send_public_key(source_public_key, nodes_before_key_exchange, destination_node):
    node_uri = str.format("http://{0}:{1}/keyShare", destination_node["hostname"], destination_node["port"])
    message = {"publicKey": source_public_key}
    onion = _create_onion(nodes_before_key_exchange, node_uri, message)
    onion_response = _send_hidden_request(onion)
    decrypted_response = decrypt_response(onion_response, nodes_before_key_exchange)

    if "success" in decrypted_response and decrypted_response["success"]:
        print(str.format("Successfully send public key to {0}", destination_node["name"]))
    else:
        print(str.format("Failed sending public key to {0}", destination_node["name"]))

    # json_data = {"source": {"hostname": source["hostname"], "port": source["port"]},
    #              "destination": ""}  # TODO NEXT_NODE_IN_PATH
    # json_data = {"publicKey": source_public_key}
    # response = requests.post(node_uri, json=json_data).json()
    #
    # # TODO maybe return None instead?
    # if not ("publicKey" in response):
    #     raise ValueError("Key sharing failure")
    # other_public_key = response["publicKey"]
    # shared_key = diffie_hellman.generate_shared_key(other_public_key)
    #
    # return shared_key


def _create_onion(path, final_destination, message):
    current_onion = {"message": message, "nextDestination": final_destination}

    for i in range(len(path)):
        next_node = path[-(i + 1)]
        next_destination = str.format("http://{0}:{1}/relay", next_node["hostname"], next_node["port"])
        shared_key = next_node["sharedKey"]
        current_onion_bytes = str(current_onion).encode("ISO-8859-1") # TODO change to iso?
        layer_algorithm, encrypted_layer = encrypt_data(current_onion_bytes, shared_key)
        next_node["encryptionAlgorithm"] = layer_algorithm
        current_onion = {"message": encrypted_layer, "nextDestination": next_destination}

    # TODO go in reverse, and add the final message to the final node and go back to create a raw onion
    # TODO go in noraml order and encrypt the previous raw onion
    # Encrypt the message according to the length of the path
    # for node in path:
    #     # Adds a layer to the onion
    #     onion_message = {"message": onion, "nextDestination": destination}
    #     onion = encrypt_data(message, node["shared_key"])
    #
    # return onion

    return current_onion


def _send_hidden_request(onion_message):
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
