from flask import Flask, request, jsonify
import sys
from src.regularServers.data import employees, salaries

"""
A server implementation which returns data for specific requests.
"""

app = Flask(__name__)


def main():
    if len(sys.argv) != 3:
        raise ValueError("hostname and port")
    hostname = sys.argv[1]
    port = sys.argv[2]
    app.run(host=hostname, port=port)


@app.route("/employees", methods=["POST"])
def get_employees():
    """
    Retrieves a list of employees.
    """
    request_data = request.get_json()

    # Check if the request is valid
    if not _is_valid_message(request_data):
        return jsonify(success=False)
    print(str.format("Received request {0}", request))

    return {"message": employees}


@app.route("/salaries", methods=["POST"])
def get_salaries():
    """
    Retrieves a list of salaries.
    """
    request_data = request.get_json()

    # Check if the request is valid
    if not _is_valid_message(request_data):
        return jsonify(success=False)
    print(str.format("Received request {0}", request))

    return {"message": salaries}


def _is_valid_message(request_data):
    """
    Checks if the given request is valid.
    :param request_data: request to check if valid
    :return: is the request valid
    """
    return request_data and request_data["message"]


if __name__ == "__main__":
    main()
