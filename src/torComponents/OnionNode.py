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
from src.torComponents.onionUtils import decrypt_data, encrypt_data, generate_unique_id, send_request

app = Flask(__name__)

# # Tell Flask to use the above defined config
# app.config.from_mapping(config)
# cache = Cache(app)

# # Create a routes list
# cache.set("routes", [])
# _routes = []
_shared_routes = {}
_connection = {}
_directory_node = {}
_diffie_hellman = DiffieHellman()


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
    _connection["publicKey"] = _diffie_hellman.get_public_key()
    _connection["salt"] = os.urandom(16).decode("ISO-8859-1")
    print(str.format("Received public key: {0}", _connection["publicKey"]))

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
    print(str.format("Publishing node {0} with public key: {1}", _connection["name"], _connection["publicKey"]))
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
    message = request_data["message"]
    other_public_key = message["publicKey"]
    print(str.format("Received public key: {0}", other_public_key))
    # connection_id = request_data["connectionId"]
    source_uri = request_data["sourceUri"]

    # Get the current node's public key to send to the other side
    # current_public_key = diffie_hellman.get_public_key()

    # Create the shared key
    shared_key = _diffie_hellman.generate_shared_key(other_public_key, _connection["salt"].encode("ISO-8859-1"))

    # Create a new route between the request's source and the current node
    shared_route = {"source": source_uri,  # "keyId": key_id,
                  "sharedKey": shared_key}
    _shared_routes[source_uri] = shared_route
    print(str.format("Added shared key with {0}, value: {1}", source_uri, shared_key))

    return jsonify(success=True)


@app.route("/removeRoute", methods=["POST"])
def remove_route():
    return None


@app.route("/relay", methods=["POST"])
def accept_relay():
    request_data = request.get_json()

    if not _is_valid_relay_request(request_data):
        return jsonify(success=False)
    #shared_route = _shared_routes[request.host_url]  # TODO check if not null
    if _is_forward_message(request_data):
        response = _pass_message(request_data)
    else:  # New route creation request
        response = None  # TODO implement reverse send

    return response


def _is_valid_key_sharing_request(request_data):
    return request_data and ("message" in request_data) and ("publicKey" in request_data["message"])


def _is_forward_message(request_data):
    return "response" not in request_data


def _is_valid_relay_request(request_data):
    return request_data and ("message" in request_data)


# def _is_route_exists(connection_id):
#     for route in _routes:
#         if route["connectionId"] == connection_id:
#             return True
#     return False


def _pass_message(request_data):
    source_uri = request_data["sourceUri"]
    shared_route = _shared_routes[source_uri] # TODO check that it's not None
    key = shared_route["sharedKey"]
    encrypted_message = request_data["message"].encode("ISO-8859-1")
    decrypted_message_bytes = decrypt_data(encrypted_message, key)
    decrypted_message_json = ast.literal_eval(decrypted_message_bytes.decode('utf-8')) # TODO should it be changed to ISO? seems to work without it
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
    # TODO convert response to bytes?
    _, encrypted_response_bytes = encrypt_data(response_bytes, key) # TODO add encryption
    encrypted_response_json = {"message": encrypted_response_bytes.decode("ISO-8859-1")}
    return encrypted_response_json


if __name__ == "__main__":
    main()
