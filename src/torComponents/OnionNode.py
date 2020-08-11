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
from src.torComponents.onionUtils import decrypt_data, generate_unique_id, send_request

app = Flask(__name__)

# # Tell Flask to use the above defined config
# app.config.from_mapping(config)
# cache = Cache(app)

# # Create a routes list
# cache.set("routes", [])
_routes = []
_shared_keys = []
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
    # connection_id = request_data["connectionId"]
    source_uri = request.host_url

    # Get the current node's public key to send to the other side
    current_public_key = diffie_hellman.get_public_key()

    # Create the shared key
    shared_key = diffie_hellman.generate_shared_key(other_public_key)

    # Create a new route between the request's source and the current node
    shared_key = {"source": source_uri,  # "keyId": key_id,
                  "sharedKey": shared_key}
    _shared_keys.append(shared_key)

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
        response = None  # TODO implement reverse send
    else:  # New route creation request
        response = _pass_message(request)

    return response


def _is_valid_key_sharing_request(request_data):
    return request_data and ("publicKey" in request_data)


def _is_valid_relay_request(request_data):
    return request_data and ("message" in request_data)


def _is_route_exists(connection_id):
    for route in _routes:
        if route["connectionId"] == connection_id:
            return True
    return False


def _pass_message(request_data):
    source = request_data.host_url  # TODO add http://?
    request_json = request_data.get_json()
    corresponding_shared_key = None
    for shared_key in _shared_keys:
        if shared_key["source"] == source:
            corresponding_shared_key = shared_key

    key = corresponding_shared_key["sharedKey"]
    encrypted_message = request_json["message"]
    decrypted_message = decrypt_data(encrypted_message, key)
    destination_uri = decrypted_message["nextDestination"]
    connection_id = generate_unique_id()
    message = {"message": decrypted_message, "connectionId": connection_id}
    response = send_request(destination_uri, message)

    return response
    # TODO the above is wrong,
    #  now the node needs to decrypt a layer but to do that it needs the shared key
    #  which was created in the session before, check where it was saved


if __name__ == "__main__":
    main()
