from tkinter import *
from tkinter import messagebox
import requests

NUM_OF_NODES_IN_PATH = 3
MINIMUM_NODES_IN_PATH = 3

root = Tk()
_uri_input = Entry(root, width=50, borderwidth=1)
_window_settings = {}
_proxy_node = {}

# TODO fix border span
# TODO allow asynchronous wait with a disabled send button click
# TODO check about closing the form
# TODO add direct fast request (optional)

def main():
    if len(sys.argv) != 3:
        raise ValueError("Expected to receive onion proxy hostname, port")
    proxy_hostname = sys.argv[1]
    proxy_port = sys.argv[2]

    _proxy_node["hostname"] = proxy_hostname
    _proxy_node["port"] = proxy_port

    # Add initial widgets
    add_widgets()

    # Run the client
    root.mainloop()


def clean_form():
    pass


def add_widgets():
    root.title("Onion Data Grabber")

    # resource_input = Entry(root, width=50, borderwidth=1)
    uri_button = Button(root, text="Get Resource", command=get_resource)

    _uri_input.grid(row=0, column=0, padx=10, pady=10, columnspan=4)
    # resource_input.grid(row=1, column=0, padx=10, pady=10)
    uri_button.grid(row=0, column=5, padx=10, pady=10)
    _uri_input.insert(0, "Enter URI")
    _window_settings["minimumRow"] = 1
    _window_settings["maximumRow"] = 1
    # resource_input.insert(0, "Enter resource")


def _clean_form():
    start_row = _window_settings["minimumRow"]
    last_row = _window_settings["maximumRow"]

    for i in range(last_row - start_row):
        current_row = start_row + i
        current_record = root.grid_slaves(row=current_row)

        for item in current_record:
            item.grid_forget()
    _window_settings["maximumRow"] = _window_settings["minimumRow"]


def get_resource():
    _clean_form()
    destination_uri = _uri_input.get()

    if not destination_uri:
        messagebox.showerror(title="Input Error", message="URI can't be empty")
        return
    destination_message = "message"

    onion_proxy_uri = str.format("http://{0}:{1}", _proxy_node["hostname"], _proxy_node["port"])
    response = requests.get(onion_proxy_uri, params={"req": destination_uri, "msg": destination_message})

    _display_response(response)


def _display_response(response):
    _clean_form()

    if not _is_valid_response(response):
        messagebox.showerror(title="Response Error", message="Unsupported response")
        return

    if _is_error_response(response):
        messagebox.showerror(title="Response Error", message="Resource not found")
        return

    response_json = response.json()
    data = response_json["message"]

    try:
        _display_table_data(data)
    except Exception:
        messagebox.showerror(title="Response Error", message="Unsupported response")


def _is_valid_response(response):
    try:
        response_json = response.json()
        return response_json and ("message" in response_json)  # TODO or not found status code)
    except Exception:
        return False


def _is_error_response(response):
    return response.status_code != 200


def _display_table_data(data):
    current_row = _window_settings["minimumRow"]

    titles_record = data[0]
    _display_titles(titles_record, current_row)
    current_row += 1

    for record in data:
        _add_table_row(record, current_row)
        current_row += 1
    _window_settings["maximumRow"] = current_row


def _display_titles(titles_record, current_row):
    keys = sorted(titles_record.keys())
    current_column = 0

    for key in keys:
        key_label = Label(root, text=key, borderwidth=2, relief="groove", font='Helvetica 10 bold')
        key_label.grid(row=current_row, column=current_column, padx=5, pady=3)
        current_column += 1


def _add_table_row(record, current_row):
    keys = sorted(record.keys())
    current_column = 0

    for key in keys:
        value_label = Label(root, text=record[key], borderwidth=2, relief="groove")
        value_label.grid(row=current_row, column=current_column, padx=5, pady=3)
        current_column += 1


if __name__ == "__main__":
    main()
