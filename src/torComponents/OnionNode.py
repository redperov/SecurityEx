from flask import Flask, request, jsonify
from flask_caching import Cache
import requests
import sys

from src.myEncryption.DiffieHellman import DiffieHellman

# config = {
#     "DEBUG": True,  # some Flask specific configs
#     "CACHE_TYPE": "simple",  # Flask-Caching related configs
#     "CACHE_DEFAULT_TIMEOUT": 300
# }
app = Flask(__name__)

# # Tell Flask to use the above defined config
# app.config.from_mapping(config)
# cache = Cache(app)

# # Create a routes list
# cache.set("routes", [])
_routes = []
_connection = {}
_directory_node = {}


def main():
    if len(sys.argv) != 6:
        raise ValueError("Expected to receive server name, hostname, port and directory node hostname, port")
    current_name = sys.argv[1]
    current_hostname = sys.argv[2]
    current_port = sys.argv[3]
    directory_hostname = sys.argv[4]
    directory_port = sys.argv[5]

    # Save the connection parameters
    # cache.set("connection", {"name": current_name, "hostname": current_hostname, "port": current_port})
    # cache.set("directory_node", {"hostname": directory_hostname, "port": directory_port})

    _connection["name"] = current_name
    _connection["hostname"] = current_hostname
    _connection["port"] = current_port
    _directory_node["hostname"] = directory_hostname
    _directory_node["port"] = directory_port
    publish_node()

    # Run the server
    app.run(host=current_hostname, port=current_port)


def publish_node():
    """
    Notify the directory node about the existence of the current node.
    """
    # connection = cache.get("connection")
    # directory_node = cache.get("directory_node")
    directory_node_uri = str.format("http://{0}:{1}/addNode",
                                    _directory_node["hostname"], _directory_node["port"])
    print("Publishing node...")
    # TODO validate the response
    response = requests.post(directory_node_uri, json=_connection).json()

    # Check if the directory node accepted the current node
    if response["success"]:
        print("Node published successfully")
    else:
        print("Failed publishing node")
        exit(1)


@app.route("/keyShare", methods=["POST"])
def key_share():
    request_data = request.get_json()

    if not _is_valid_key_sharing_request(request_data):
        return jsonify(success=False)
    diffie_hellman = DiffieHellman()
    other_public_key = request_data["publicKey"]
    connection_id = request_data["connectionId"]
    source_uri = request.host_url

    # Get the current node's public key to send to the other side
    current_public_key = diffie_hellman.get_public_key()

    # Create the shared key
    encryption_algorithm, shared_key = diffie_hellman.generate_shared_key(other_public_key)

    # Create a new route between the request's source and the current node
    route = {"source": source_uri, "connectionId": connection_id,
             "encryptionAlgorithm": encryption_algorithm, "sharedKey": shared_key}
    _routes.append(route)

    return {"publicKey": current_public_key}


@app.route("/removeRoute", methods=["POST"])
def remove_route():
    return None


@app.route("/relay", methods=["POST"])
def accept_relay():
    request_data = request.get_json()

    if not _is_valid_relay_request(request_data):
        return jsonify(success=False)
    if _is_route_exists(request_data["connectionId"]):
        response = None # TODO implement reverse send
    else: # New route creation request
        response = _pass_message(request_data)

    return response


def _is_valid_key_sharing_request(request_data):
    return request_data and request_data["publicKey"] and request_data["connectionId"]


def _is_valid_relay_request(request_data):
    return request_data and request_data["message"]


def _is_route_exists(connection_id):
    for route in _routes:
        if route["connectionId"] == connection_id:
            return True
    return False


def _pass_message(request_data):
    connection_id = request_data["connectionId"]
    corresponding_route = None
    for route in _routes:
        if route["connectionId"] == connection_id:
            corresponding_route = request_data
    print()
    # TODO the above is wrong,
    #  now the node needs to decrypt a layer but to do that it needs the shared key
    #  which was created in the session before, check where it was saved

if __name__ == "__main__":
    main()
