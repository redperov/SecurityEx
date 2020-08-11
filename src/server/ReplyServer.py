from flask import Flask, request, jsonify
import sys

app = Flask(__name__)


def main():
    if len(sys.argv) != 3:
        raise ValueError("hostname and port")
    hostname = sys.argv[1]
    port = sys.argv[2]
    app.run(host=hostname, port=port)


@app.route("/reply", methods=["POST"])
def reply():
    request_data = request.get_json()

    # Check if the request is valid
    if not _is_valid_message(request_data):
        return jsonify(success=False)
    message = request_data["message"]
    reply = message.upper()

    return {"message": reply}


def _is_valid_message(request_data):
    return request_data and request_data["message"]


if __name__ == "__main__":
    main()
