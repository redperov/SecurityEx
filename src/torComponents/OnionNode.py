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
    if len(sys.argv) != 5:
        raise ValueError("Expected to receive server name, hostname, port and directory node hostname, port")
    current_name = sys.argv[0]
    current_hostname = sys.argv[1]
    current_port = sys.argv[2]
    directory_hostname = sys.argv[3]
    directory_port = sys.argv[4]

    # Save the connection parameters
    # cache.set("connection", {"name": current_name, "hostname": current_hostname, "port": current_port})
    # cache.set("directory_node", {"hostname": directory_hostname, "port": directory_port})

    _connection = {"name": current_name, "hostname": current_hostname, "port": current_port}
    _directory_node = {"hostname": directory_hostname, "port": directory_port}

    # Run the server
    app.run(host=current_hostname, port=current_port)
    publish_node()


def publish_node():
    """
    Notify the directory node about the existence of the current node.
    """
    # connection = cache.get("connection")
    # directory_node = cache.get("directory_node")
    directory_node_uri = str.format("http://{0}:{0}/addNode",
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


@app.route("/establishRoute", methods=["POST"])
def establish_route():
    request_data = request.get_json()

    if not _is_valid_establish_route_request(request_data):
        return jsonify(success=False)
    diffie_hellman = DiffieHellman()
    other_public_key = request_data["publicKey"]
    source = request_data["source"]
    destination = request_data["destination"]

    # Get the current node's public key to send to the other side
    current_public_key = diffie_hellman.get_public_key()

    # Create the shared key
    shared_key = diffie_hellman.generate_shared_key(other_public_key)
    new_route = {"source": source, "destination": destination, "shared_key": shared_key}

    # TODO handle a case of race condition?
    #routes = cache.get("routes")
    _routes.append(new_route)
    #cache.set("routes", routes)

    return {"publicKey": current_public_key}


@app.route("/removeRoute", methods=["POST"])
def remove_route():
    return None


@app.route("/relay", methods=["POST"])
def accept_relay():
    return None


def _is_valid_establish_route_request(request_data):
    return request_data and request_data["publicKey"] and request_data["source"] and request_data["destination"]


if __name__ == "__main__":
    main()
