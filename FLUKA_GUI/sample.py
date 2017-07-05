#!/usr/bin/env python

try:
    import tkinter
except ImportError:
    import Tkinter as tkinter
import _tkinter
import platform

class TextBoxDemo(tkinter.Tk):
    def __init__(self, parent):
        tkinter.Tk.__init__(self, parent)
        self.parent = parent
        self.wm_title("TextBoxDemo")
        self.textbox = tkinter.Text(self)
        self.textbox.pack()

        self.txt_var = tkinter.StringVar()
        self.entry = tkinter.Entry(self, textvariable=self.txt_var)
        self.entry.pack(anchor="w")

        self.button = tkinter.Button(self, text="Add", command=self.add)
        self.button.pack(anchor="e")


    def add(self):
        self.textbox.insert(tkinter.END, self.txt_var.get())


if __name__ == '__main__':
    try:
        app = TextBoxDemo(None)
        app.mainloop()
    except _tkinter.TclError as e:
        if platform.system() == 'Windows':
            print(e)
            print("Seems tkinter will not run; try running this program outside a virtualenv.")
