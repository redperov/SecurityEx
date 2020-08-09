from flask import Flask, request, jsonify
import requests
import sys
import random

from src.myEncryption.DiffieHellman import DiffieHellman

app = Flask(__name__)
_connection = {}
_directory_node = {}
NUM_OF_NODES_IN_PATH = 3
MINIMUM_NODES_IN_PATH = 3
diffie_hellman = DiffieHellman()


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
    destination_uri = request["req"]
    path = _choose_path(NUM_OF_NODES_IN_PATH)
    _create_shared_keys(path)
    onion_message = _create_onion(path, destination_uri)


def _is_valid_args(args):
    return args and args["req"]


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

    return chosen_path


def _create_shared_keys(nodes):
    print("Performing key sharing...")

    # TODO maybe exchange the prime and modulus in the beginning to make it look real?
    current_public_key = diffie_hellman.get_public_key()

    for node in nodes:
        shared_key = _create_shared_key(current_public_key, node)
        node["shared_key"] = shared_key
    print("Finished key sharing")

    return nodes


def _create_shared_key(source_public_key, destination):
    node_uri = str.format("http://{0}:{0}/keyShare", destination["hostname"], destination["port"])
    # json_data = {"source": {"hostname": source["hostname"], "port": source["port"]},
    #              "destination": ""}  # TODO NEXT_NODE_IN_PATH
    json_data = {"publicKey": source_public_key}
    response = requests.post(node_uri, json_data=json_data).json()

    # TODO maybe return None instead?
    if not response["publicKey"]:
        raise ValueError("Key sharing failure")
    other_public_key = response["publicKey"]
    shared_key = diffie_hellman.generate_shared_key(other_public_key)

    return shared_key


def _create_onion(path, message):
    onion = None

    # Encrypt the message according to the length of the path
    for node in path:
        onion = _add_layer(message, node["shared_key"])

    return onion


def _add_layer(message, encryption_key):
    return None


if __name__ == "__main__":
    main()
