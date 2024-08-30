# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 08:47:56 2024

@author: tbates
"""
import tkinter as tk
from tkinter import simpledialog, messagebox

class TextLogger:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)
        self.input_value = None

    def write(self, message):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message)
        self.text_widget.config(state=tk.DISABLED)
        self.text_widget.see(tk.END)  # Auto-scroll to the end
        self.text_widget.focus()

    def flush(self):
        pass  # This is needed for file-like object compatibility

    def read_input(self):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, "\n> ")
        self.text_widget.config(state=tk.NORMAL)
        self.input_value = tk.StringVar()
        self.text_widget.bind("<Return>", self.capture_input)
        self.text_widget.bind("<Escape>",self.capture_input)
        self.text_widget.master.wait_variable(self.input_value)
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.focus()
        return self.input_value.get()

    def capture_input(self, event):
        # Get user input from the text widget
        input_text = self.text_widget.get("insert linestart", "insert lineend").strip()
        if input_text.startswith("> "):
            input_text = input_text[2:]  # Remove the '> ' prompt
        self.input_value.set(input_text)

        # Insert the captured input into the text widget
        self.text_widget.insert(tk.END, "\n")
        self.text_widget.see(tk.END)  # Scroll to the end of the text widget
 
        # Unbind the <Return> key
        self.text_widget.unbind("<Return>")
    
    def end_test(self, event=None):
        messagebox.showinfo('Restart','Restart test when ready')
        # Unbind the <Return> key used for restarting the test
        self.text_widget.unbind("<Return>")
        # Clear the text widget and reset for new test
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)

        