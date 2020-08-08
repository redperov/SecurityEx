from flask import Flask, request, jsonify
from flask_caching import Cache
import requests
import sys

config = {
    "DEBUG": True,  # some Flask specific configs
    "CACHE_TYPE": "simple",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}
app = Flask(__name__)

# Tell Flask to use the above defined config
app.config.from_mapping(config)
cache = Cache(app)

# Create a paths list
cache.set("paths", [])


def main():
    if len(sys.argv) != 5:
        raise ValueError("Expected to receive server name, hostname, port and directory node hostname, port")
    current_name = sys.argv[0]
    current_hostname = sys.argv[1]
    current_port = sys.argv[2]
    directory_hostname = sys.argv[3]
    directory_port = sys.argv[4]

    # Save the connection parameters
    cache.set("connection", {"name": current_name, "hostname": current_hostname, "port": current_port})
    cache.set("directory_node", {"hostname": directory_hostname, "port": directory_port})

    # Run the server
    app.run(host=current_hostname, port=current_port)
    publish_node()


def publish_node():
    """
    Notify the directory node about the existence of the current node.
    """
    connection = cache.get("connection")
    directory_node = cache.get("directory_node")
    directory_node_uri = str.format("http://{0}:{0}/addNode",
                                    directory_node["hostname"], directory_node["port"])
    print("Publishing node...")
    response = requests.post(directory_node_uri, json=connection).json()

    # Check if the directory node accepted the current node
    if response["success"]:
        print("Node published successfully")
    else:
        print("Failed publishing node")
        exit(1)


@app.route("/establishPath", methods=["POST"])
def establish_path():
    return None


@app.route("removePath", methods=["POST"])
def remove_path():
    return None


@app.route("/relay", methods=["POST"])
def accept_relay():
    return None


if __name__ == "__main__":
    main()
