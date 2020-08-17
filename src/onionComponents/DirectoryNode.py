from flask import Flask, request, jsonify
import sys

"""
An implementation of a directory node. 
Its purpose is to keep records of the nodes in the system.
"""

app = Flask(__name__)

# Nodes in the system
_nodes = {}


def main():
    if len(sys.argv) != 3:
        raise ValueError("hostname and port")
    hostname = sys.argv[1]
    port = sys.argv[2]
    app.run(host=hostname, port=port)


@app.route("/addNode", methods=["POST"])
def add_node():
    """
    Adds a new node to the directory.
    """
    node = request.get_json()

    # Check if the request contains a valid node
    if not _is_valid_node(node):
        return jsonify(success=False)

    # Add the new node to the existing ones
    sender_uri = str.format("{0}:{1}", node["hostname"], node["port"])
    _nodes[sender_uri] = node
    print(str.format("Added new node: {0}", node))

    return jsonify(success=True)


@app.route("/getAllNodes", methods=["GET"])
def get_all_nodes():
    """
    Retrieves all the nodes in the directory.
    :return:
    """
    return {"nodes": list(_nodes.values())}


def _is_valid_node(node):
    """
    Checks if the given node is valid.
    :param node: node to check
    :return: is the node valid
    """
    return node and ("name" in node) and ("hostname" in node) and ("port" in node)


if __name__ == "__main__":
    main()
