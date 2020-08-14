from flask import Flask, request, jsonify
import sys
from flask_caching import Cache

# config = {
#     "DEBUG": True,  # some Flask specific configs
#     "CACHE_TYPE": "simple",  # Flask-Caching related configs
#     "CACHE_DEFAULT_TIMEOUT": 300
# }
app = Flask(__name__)

# # Tell Flask to use the above defined config
# app.config.from_mapping(config)
# cache = Cache(app)
#
# # Create a nodes list
# cache.set("nodes", [])
_nodes = {}


def main():
    if len(sys.argv) != 3:
        raise ValueError("hostname and port")
    hostname = sys.argv[1]
    port = sys.argv[2]
    app.run(host=hostname, port=port)


@app.route("/addNode", methods=["POST"])
def add_node():
    node = request.get_json()

    # Check if the request contains a valid node
    if not _is_valid_node(node):
        return jsonify(success=False)

    # Add the new node to the existing ones
    # nodes = cache.get("nodes")
    sender_uri = str.format("{0}:{1}", node["hostname"], node["port"])
    _nodes[sender_uri] = node
    # cache.set("nodes", nodes)
    print(str.format("Added new node: {0}", node))

    return jsonify(success=True)


@app.route("/getAllNodes", methods=["GET"])
def get_all_nodes():
    # nodes = cache.get("nodes")
    return {"nodes": list(_nodes.values())}


def _is_valid_node(node):
    return node and ("name" in node) and ("hostname" in node) and ("port" in node)


if __name__ == "__main__":
    main()
