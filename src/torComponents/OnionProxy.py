from flask import Flask, request, jsonify
import requests
import sys
import random

from src.myEncryption.DiffieHellman import DiffieHellman

app = Flask(__name__)
_connection = {}
_directory_node = {}
NUM_OF_NODES_IN_PATH = 3
diffie_hellman = DiffieHellman()


def main():
    if len(sys.argv) != 5:
        raise ValueError("Expected to receive server name, hostname, port and directory node hostname, port")
    current_name = sys.argv[0]
    current_hostname = sys.argv[1]
    current_port = sys.argv[2]
    directory_hostname = sys.argv[3]
    directory_port = sys.argv[4]

    # # Save the connection parameters
    # cache.set("connection", {"name": current_name, "hostname": current_hostname, "port": current_port})
    # cache.set("directory_node", {"hostname": directory_hostname, "port": directory_port})

    _connection = {"name": current_name, "hostname": current_hostname, "port": current_port}
    _directory_node = {"hostname": directory_hostname, "port": directory_port}

    # Run the server
    app.run(host=current_hostname, port=current_port)


@app.route("/", methods=["GET"])
def hide_request():
    print(request)
    path = choose_path(NUM_OF_NODES_IN_PATH)
    create_shared_keys(path)


def choose_path(path_length):
    directory_node_uri = str.format("http://{0}:{0}/getAllNodes",
                                    _directory_node["hostname"], _directory_node["port"])
    # TODO validate the response
    response = requests.get(directory_node_uri).json()
    nodes = response["nodes"]

    if len(nodes) < path_length:
        raise ValueError("Path size is larger than the number of available nodes")
    chosen_path = []

    for i in range(path_length):
        chosen_node = random.choice(nodes)
        chosen_path.append(chosen_node)
        nodes.remove(chosen_node)

    return chosen_path


def create_shared_keys(nodes):
    for node in nodes:
        shared_key = create_shared_key(node)
        node["shared_key"] = shared_key

    return nodes


def create_shared_key(node):
    node_uri = str.format("http://{0}:{0}/establishRoute", node["hostname"], node["port"])
    json_data = {"source": {"hostname": _connection["hostname"], "port": _connection["port"]},
                 "destination": ""} # TODO NEXT_NODE_IN_PATH
    response = requests

if __name__ == "__main__":
    main()
