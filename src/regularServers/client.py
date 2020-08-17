from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Progressbar

import requests
import threading

"""
A user interface to use the system.
"""

# Constants
NUM_OF_NODES_IN_PATH = 3
MINIMUM_NODES_IN_PATH = 3

root = Tk()

# Widgets
_uri_input = Entry(root, width=50, borderwidth=1)
_uri_button = Button(root, text="Get Resource")
_progress_bar = Progressbar(root, orient=HORIZONTAL, mode="determinate")

# Hold configurations
_window_settings = {}
_proxy_node = {}


def main():
    if len(sys.argv) != 3:
        raise ValueError("Expected to receive onion proxy hostname, port")
    proxy_hostname = sys.argv[1]
    proxy_port = sys.argv[2]

    # Save the received configurations
    _proxy_node["hostname"] = proxy_hostname
    _proxy_node["port"] = proxy_port

    # Add initial widgets
    add_widgets()

    # Run the client
    root.mainloop()


def add_widgets():
    """
    Adds the widgets to the form and initializes additional values.
    """
    root.title("Onion Data Grabber")
    root.geometry("500x400")

    _uri_input.grid(row=0, column=0, padx=10, pady=10, columnspan=4)
    _uri_button.grid(row=0, column=5, padx=10, pady=10)
    _uri_button["command"] = anonymous_button_click
    _uri_input.insert(0, "Enter URI")
    _progress_bar.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
    _progress_bar.grid_remove()
    _window_settings["minimumRow"] = 2
    _window_settings["maximumRow"] = 2


def anonymous_button_click():
    """
    Activates the request process.
    """
    _uri_button['state'] = DISABLED
    _progress_bar.grid()
    _progress_bar.start()
    request_thread = threading.Thread(target=get_resource_anonymous)
    request_thread.start()


def _clean_form():
    """
    Restores the form to its initial state.
    """
    start_row = _window_settings["minimumRow"]
    last_row = _window_settings["maximumRow"]

    for i in range(last_row - start_row):
        current_row = start_row + i
        current_record = root.grid_slaves(row=current_row)

        for item in current_record:
            item.grid_forget()
    _window_settings["maximumRow"] = _window_settings["minimumRow"]


def get_resource_anonymous():
    """
    Requests a resource in an anonymous way.
    """
    try:
        _clean_form()
        destination_uri = _uri_input.get()

        if not destination_uri:
            messagebox.showerror(title="Input Error", message="URI can't be empty")
            return
        destination_message = "message"

        # Perform the HTTP request
        onion_proxy_uri = str.format("http://{0}:{1}", _proxy_node["hostname"], _proxy_node["port"])
        response = requests.get(onion_proxy_uri, params={"req": destination_uri, "msg": destination_message})

        # Display the response to the user
        _display_response(response)
        _progress_bar.grid_remove()
        _uri_button['state'] = ACTIVE
    except Exception as e:
        print(e)
        _progress_bar.grid_remove()
        messagebox.showerror(title="Server Error", message="Can't bring resource")
        _uri_button['state'] = ACTIVE


def _display_response(response):
    """
    Displays the given response on the form.
    :param response: request response to display on the form
    """
    _clean_form()

    if not _is_valid_response(response):
        messagebox.showerror(title="Response Error", message="Unsupported response")
        return

    if _is_error_response(response):
        messagebox.showerror(title="Response Error", message="Resource not found")
        return

    # Extract the message from the response
    response_json = response.json()
    data = response_json["message"]

    try:
        _display_table_data(data)
    except Exception:
        messagebox.showerror(title="Response Error", message="Unsupported response")


def _is_valid_response(response):
    """
    Check if the response is valid.
    :param response: response to check
    :return: is the response valid
    """
    try:
        response_json = response.json()
        return response_json and ("message" in response_json)
    except Exception:
        return False


def _is_error_response(response):
    """
    Checks if the response is an error.
    :param response: response to check
    :return: is the response an error
    """
    return response.status_code != 200


def _display_table_data(data):
    """
    Displays the given data in a table.
    :param data: data to display in a table
    """
    current_row = _window_settings["minimumRow"]

    # Add titles to the table
    titles_record = data[0]
    _display_titles(titles_record, current_row)
    current_row += 1

    # Add a table row for each record in the data
    for record in data:
        _add_table_row(record, current_row)
        current_row += 1
    _window_settings["maximumRow"] = current_row


def _display_titles(titles_record, current_row):
    """
    Displays titles above the corresponding data columns.
    :param titles_record: titles of the columns
    :param current_row: the form row at which the titles will be added
    """
    keys = sorted(titles_record.keys())
    current_column = 0

    for key in keys:
        key_label = Label(root, text=key, borderwidth=2, relief="groove", font='Helvetica 10 bold')
        key_label.grid(row=current_row, column=current_column, padx=10, sticky="ew")
        current_column += 1


def _add_table_row(record, current_row):
    """
    Adds a single table row of data
    :param record: contains the data to display in the row
    :param current_row:the form row at which the record will be added
    :return:
    """
    keys = sorted(record.keys())
    current_column = 0

    for key in keys:
        value_label = Label(root, text=record[key], borderwidth=2, relief="groove")
        value_label.grid(row=current_row, column=current_column, padx=10, sticky="ew")
        current_column += 1


if __name__ == "__main__":
    main()
