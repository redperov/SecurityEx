from tkinter import *
from tkinter import messagebox

root = Tk()
root.title("Onion Data Grabber")


def clean_form():
    pass


def get_resource():
    clean_form()
    uri_text = uri_input.get()

    if not uri_text:
        messagebox.showerror(title="Input Error", message="URI can't be empty")



uri_input = Entry(root, width=50, borderwidth=1)
# resource_input = Entry(root, width=50, borderwidth=1)
uri_button = Button(root, text="Get Resource", command=get_resource)
uri_input.grid(row=0, column=0, padx=10, pady=10)
# resource_input.grid(row=1, column=0, padx=10, pady=10)
uri_button.grid(row=1, column=0, padx=10, pady=10)
uri_input.insert(0, "Enter URI")
# resource_input.insert(0, "Enter resource")

root.mainloop()
