# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:03:56 2024

@author: tbates
"""

import os
import sys
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import automation1 as a1
import socket
import gc
import time
import json
import ctypes
import queue

from RotaryCalTest import rotary_cal
from AngularTest import angular
from plot_manager import PlotManager

sys.path.append(r"K:\10. Released Software\Systems Manufacturing Support\Shared")
#sys.path.append(r"C:\Users\tbates\Python\shared")
from Logger import TextLogger

# Define Automation1 Studio-inspired color palette
BACKGROUND = "#F0F0F0"  # Light gray background
WHITE = "#FFFFFF"  # Pure white for input fields
BLUE_PRIMARY = "#0078D4"  # Aerotech blue
BLUE_HOVER = "#106EBE"  # Slightly darker blue for hover
BLUE_ACTIVE = "#005A9E"  # Darker blue for clicking
TEXT_PRIMARY = "#252423"  # Darker gray for primary text
TEXT_SECONDARY = "#484644"  # Medium gray for secondary text
BORDER = "#E1E1E1"  # Light border color
DISABLED_BG = "#F3F2F1"  # Slightly darker than background for disabled
DISABLED_FG = "#A19F9D"  # Muted text for disabled elements

# Initialize global variables and states
yrawforward = []
zrawforward = []
yrawreverse = []
zrawreverse = []
xforwarddata = []
xreversedata = []
yforwarddata = []
yreversedata = []
zforwarddata = []
zreversedata = []
plot_mean = 0
col_axis_X = ''
col_axis_Y = ''
clientsocket = None
forward_queue = queue.Queue()
reverse_queue = queue.Queue()
server_ready_event = threading.Event()
test_thread = None
server_thread = None
controller = None
is_plot_running = False
server_running = True

# Add global variables for UI controls
unit_var = None
col_axis_var = None
drive_var = None
direction = None

# Define the application name and user data file path
APP_NAME = "ManualRotary"
USER_DATA_DIR = os.path.join(os.getenv('APPDATA'), APP_NAME)
USER_DATA_FILE = os.path.join(USER_DATA_DIR, "user_data.json")

# Ensure the directory exists
os.makedirs(USER_DATA_DIR, exist_ok=True)

def save_user_inputs(data):
    """Save user inputs to a JSON file."""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_user_inputs():
    """Load user inputs from a JSON file."""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def controller_def():
    ver = tk.Toplevel(window)
    ver.title('Connection Type')
    ver.configure(bg=WHITE)

    custom_font = font.Font(family="Segoe UI", size=12, weight="bold")

    label = tk.Label(ver, text="Are you trying to connect via USB?", bg=WHITE, font=custom_font, fg=TEXT_PRIMARY)
    label.grid(row=0, column=0, columnspan=2, padx=10, pady=5)

    def on_yes():
        ver.result = 'yes'
        ver.destroy()

    def on_no():
        ver.result = 'No'
        ver.destroy()

    button_ok = ttk.Button(ver, text="Yes", width=10, command=on_yes, style='Primary.TButton')
    button_ok.grid(row=4, column=0, padx=10, pady=10)

    button_cancel = ttk.Button(ver, text="No", width=10, command=on_no, style='Secondary.TButton')
    button_cancel.grid(row=4, column=1, padx=10, pady=10)

    ver.resizable(False, False)
    ver.update_idletasks()

    screen_width = ver.winfo_screenwidth()
    screen_height = ver.winfo_screenheight()
    ver_width = ver.winfo_reqwidth()
    ver_height = ver.winfo_reqheight()
    x_cordinate = int((screen_width / 2) - (ver_width / 2))
    y_cordinate = int((screen_height / 2) - (ver_height / 2))

    ver.geometry("{}x{}+{}+{}".format(ver_width, ver_height, x_cordinate, y_cordinate))
    ver.focus_set()
    ver.result = None
    ver.wait_window()

    return ver.result

def unit_def(*args):
    """Define the unit of measurement based on the selection."""
    global units, unit_var
    if unit_var and unit_var.get() == "deg":
        units = 'deg'
    elif unit_var and unit_var.get() == "arcmin":
        units = 'arcmin'
    elif unit_var and unit_var.get() == "arcsec":
        units = 'arcsec'
    else:
        units = 'None'

def col_axis_def(*args):
    """Define the column axis based on the selection."""
    global col_axis_X, col_axis_Y, col_axis_var
    if col_axis_var and col_axis_var.get() == "X":
        col_axis_X = "X"
        col_axis_Y = "Y"
    elif col_axis_var and col_axis_var.get() == "Y":
        col_axis_X = "Y"
        col_axis_Y = "Z"
    elif col_axis_var and col_axis_var.get() == "Z":
        col_axis_X = "Z"
        col_axis_Y = "X"
    else:
        col_axis_X = ""
        col_axis_Y = ""

def drive_def(*args):
    """Define the drive type based on the selection."""
    global drive, drive_var
    if drive_var and drive_var.get() == "USB":
        drive = 'USB'
    elif drive_var and drive_var.get() == "A1":
        drive = 'A1'
    else:
        drive = 'None'

def test_type_def(test_type_value):
    """Define the test type based on the selection."""
    global test_type, is_cal
    test_type = test_type_value
    if test_type == 'cal':
        is_cal = 1
    else:
        is_cal = 0

def start_test(input_frame):
    """Start button callback"""
    try:
        # Disable run button
        for widget in input_frame.winfo_children():
            if isinstance(widget, ttk.Button) and widget['text'] == 'Run Test':
                widget.config(state=tk.DISABLED)
                break
        
        # Get test parameters
        axis = str(input_frame.winfo_children()[input_frame.axis_row].winfo_children()[1].get())
        step_size = float(input_frame.winfo_children()[input_frame.step_row].winfo_children()[1].get())
        travel = float(input_frame.winfo_children()[input_frame.travel_row].winfo_children()[1].get())
        st_serial = str(input_frame.winfo_children()[input_frame.job_row].winfo_children()[1].get())
        comments = str(input_frame.winfo_children()[input_frame.comm_row].winfo_children()[1].get())
        stage = str(input_frame.winfo_children()[input_frame.stage_row].winfo_children()[1].get())
        op = str(input_frame.winfo_children()[input_frame.op_row].winfo_children()[1].get())
        
        # Get the appropriate plot manager based on the test type
        if test_type == 'cal':
            plot_manager = rot_plot_manager
            test_class = rotary_cal
        else:  # Angular test
            plot_manager = ang_plot_manager
            test_class = angular
        
        # Initialize plot
        if test_type == 'cal':
            plot_manager.setup_plot(axis)
        else:
            plot_manager.setup_plot(axis, col_axis_X, col_axis_Y)
        
        # Run the test
        test_instance = test_class(
            axis, step_size, travel, units, test_type, st_serial, 
            comments, stage, op, txt_outStr if test_type == 'cal' else txt_outStr1,
            window
        )
        
        # Set up data callback
        def on_data_update(positions, measurements, reverse_data=None, axis_num=None):
            plot_manager.update_plot(positions, measurements, reverse_data, axis_num)
        
        # Start the test with the callback
        test_instance.setup_test(on_data_update)
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start test: {str(e)}")
        # Re-enable run button
        for widget in input_frame.winfo_children():
            if isinstance(widget, ttk.Button) and widget['text'] == 'Run Test':
                widget.config(state=tk.NORMAL)
                break

def import_data(input_frame):
    """Import data from a file."""
    try:
        # Get test parameters
        axis = str(input_frame.winfo_children()[input_frame.axis_row].winfo_children()[1].get())
        step_size = float(input_frame.winfo_children()[input_frame.step_row].winfo_children()[1].get())
        travel = float(input_frame.winfo_children()[input_frame.travel_row].winfo_children()[1].get())
        st_serial = str(input_frame.winfo_children()[input_frame.job_row].winfo_children()[1].get())
        comments = str(input_frame.winfo_children()[input_frame.comm_row].winfo_children()[1].get())
        stage = str(input_frame.winfo_children()[input_frame.stage_row].winfo_children()[1].get())
        op = str(input_frame.winfo_children()[input_frame.op_row].winfo_children()[1].get())
        
        # Get the appropriate test class based on the test type
        if test_type == 'cal':
            test_class = rotary_cal
            text_widget = txt_outStr
        else:  # Angular test
            test_class = angular
            text_widget = txt_outStr1
        
        # Run the test
        test_instance = test_class(
            axis, step_size, travel, units, test_type, st_serial, 
            comments, stage, op, text_widget, window
        )
        test_instance.setup_test()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import data: {str(e)}")

def open_rotary_Plot():
    """Open a new window with the rotary calibration plot."""
    plot_window = tk.Toplevel(window)
    plot_window.title("Rotary Calibration Plot")
    plot_window.configure(bg=BACKGROUND)
    
    # Create plot frame
    plot_frame = ttk.Frame(plot_window, padding="10 10 10 10", style='Card.TFrame')
    plot_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
    
    # Configure plot frame grid
    plot_frame.grid_rowconfigure(0, weight=1)
    plot_frame.grid_columnconfigure(0, weight=1)
    
    # Initialize plot manager for the new window
    plot_manager = PlotManager(plot_window, plot_frame, plot_type='rotary')
    plot_manager.setup_plot("Rotary Calibration")
    
    # Size and position the window
    width = 800
    height = 600
    screen_width = plot_window.winfo_screenwidth()
    screen_height = plot_window.winfo_screenheight()
    x_cordinate = int((screen_width/2) - (width/2))
    y_cordinate = int((screen_height/2) - (height/2))
    plot_window.geometry(f"{width}x{height}+{x_cordinate}+{y_cordinate}")
    
    # Configure window grid
    plot_window.grid_rowconfigure(0, weight=1)
    plot_window.grid_columnconfigure(0, weight=1)
    plot_window.focus_set()

def UI():
    global window, plot_manager, test_type, units, drive, is_cal
    
    # Initialize global variables
    test_type = 'None'
    units = 'deg'
    drive = 'None'
    is_cal = 0
    plot_manager = None
    
    # Load stored user inputs
    stored_data = load_user_inputs()
    
    # Initialize Tkinter window with Automation1 styling
    window = tk.Tk()
    window.title("Rotary and Angular Testing")
    window.configure(bg=BACKGROUND)

    # Create and configure style
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configure modern styles for ttk widgets
    style.configure('TButton', 
                   padding=10, 
                   font=('Segoe UI', 10),
                   background=BLUE_PRIMARY,
                   foreground=WHITE)
    
    style.configure('TLabel',
                   font=('Segoe UI', 10),
                   background=BACKGROUND,
                   foreground=TEXT_PRIMARY)
    
    style.configure('TEntry',
                   padding=2,  # Reduced from 3
                   font=('Segoe UI', 9),
                   width=15,  # Set default width for entry fields
                   foreground=TEXT_PRIMARY)
    
    style.configure('TOptionMenu',
                   padding=5,
                   font=('Segoe UI', 10),
                   foreground=TEXT_PRIMARY)
    
    # Additional modern styles
    style.configure('Card.TFrame',
                   background=BACKGROUND,
                   relief='solid',
                   borderwidth=1)
    
    style.configure('Header.TLabel',
                   font=('Segoe UI', 12, 'bold'),
                   foreground=TEXT_PRIMARY,
                   background=WHITE)
    
    style.configure('Field.TLabel',
                   font=('Segoe UI', 10),
                   background=WHITE,
                   foreground=TEXT_PRIMARY)
    
    style.configure('Modern.TEntry',
                   padding=2,  # Reduced from 3
                   relief='solid',
                   borderwidth=1,
                   width=15,  # Set default width for entry fields
                   foreground=TEXT_PRIMARY)
    
    style.configure('Modern.TRadiobutton',
                   background=BACKGROUND,  # Match parent background
                   font=('Segoe UI', 10),
                   foreground=TEXT_PRIMARY)
    
    style.configure('Modern.TCheckbutton',
                   background=BACKGROUND,  # Match parent background
                   font=('Segoe UI', 10),
                   foreground=TEXT_PRIMARY)
    
    # Add map configuration for Modern.TCheckbutton to handle disabled state
    style.map('Modern.TCheckbutton',
              background=[('disabled', BACKGROUND)],  # Keep same background when disabled
              foreground=[('disabled', DISABLED_FG)])  # Use disabled text color
    
    style.configure('Modern.TMenubutton',
                   padding=5,
                   relief='solid',
                   background=WHITE,
                   foreground=TEXT_PRIMARY)
    
    style.configure('Primary.TButton',
                   background=BLUE_PRIMARY,
                   foreground=WHITE,
                   padding=10,
                   font=('Segoe UI', 10, 'bold'))
    
    style.configure('Secondary.TButton',
                   background=BACKGROUND,
                   foreground=BLUE_PRIMARY,
                   padding=10,
                   font=('Segoe UI', 10))
    
    style.configure('TSeparator',
                   background=BORDER)

    # Configure notebook style
    style.configure("TNotebook", 
                   background=BACKGROUND,
                   borderwidth=0)
    
    style.configure("TNotebook.Tab", 
                   font=('Segoe UI', '12', 'bold'),
                   padding=[15, 5],
                   background=WHITE,
                   foreground=TEXT_PRIMARY)
    
    style.map("TNotebook.Tab",
              background=[("selected", BLUE_PRIMARY)],
              foreground=[("selected", WHITE)])

    # Window sizing and positioning
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    usable_width = ctypes.windll.user32.GetSystemMetrics(78)
    usable_height = ctypes.windll.user32.GetSystemMetrics(79)
    
    window_width = min(1900, usable_width)
    window_height = min(1000, usable_height)
    
    x_coordinate = (screen_width - window_width) // 2
    y_coordinate = 10
    
    window.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
    window.lift()
    window.focus_force()
    window.resizable(True, False)

    # Create notebook for tabs
    interface = ttk.Notebook(window)
    interface.pack(fill='both', expand=True)

    # Create frames for each tab
    tab1 = ttk.Frame(interface, style='Card.TFrame')
    tab2 = ttk.Frame(interface, style='Card.TFrame')

    # Add tabs to notebook
    interface.add(tab1, text='Rotary Cal')
    interface.add(tab2, text='Angular Testing')

    # Configure main grid for both tabs
    for tab in (tab1, tab2):
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=0)
        tab.grid_columnconfigure(1, weight=1)

    # Create input frames for both tabs
    input_frame_width = 850  # Reduced from 1000
    input_frame_height = 800  # Increased from 750

    rot_input_frame = ttk.Frame(
        tab1,
        padding="10 10 10 10",
        style='Card.TFrame',
        width=input_frame_width,
        height=input_frame_height
    )
    rot_input_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)  # Reduced padding
    
    ang_input_frame = ttk.Frame(
        tab2,
        padding="10 10 10 10",
        style='Card.TFrame',
        width=input_frame_width,
        height=input_frame_height
    )
    ang_input_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)  # Reduced padding

    # Create plot frames with increased width
    plot_frame_width = 900  # Increased from 700
    
    rot_plot_frame = ttk.Frame(tab1, padding="10 10 10 10", style='Card.TFrame', width=plot_frame_width)
    rot_plot_frame.grid(row=0, column=1, rowspan=2, sticky='nsew', padx=10, pady=10)
    
    ang_plot_frame = ttk.Frame(tab2, padding="10 10 10 10", style='Card.TFrame', width=plot_frame_width)
    ang_plot_frame.grid(row=0, column=1, rowspan=2, sticky='nsew', padx=10, pady=10)

    # Configure plot frames
    for frame in (rot_plot_frame, ang_plot_frame):
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_propagate(False)  # Prevent frame from shrinking

    # Initialize plot managers
    rot_plot_manager = PlotManager(window, rot_plot_frame, plot_type='rotary')
    ang_plot_manager = PlotManager(window, ang_plot_frame, plot_type='angular')

    # Create text output frames
    rot_text_frame = ttk.Frame(tab1, padding="10 10 10 10", style='Card.TFrame')
    rot_text_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
    
    ang_text_frame = ttk.Frame(tab2, padding="10 10 10 10", style='Card.TFrame')
    ang_text_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

    # Configure text widgets
    txt_outStr = tk.Text(
        rot_text_frame,
        wrap=tk.WORD,
        font=('Consolas', 10),
        fg=TEXT_PRIMARY,
        bg=WHITE,
        insertbackground=TEXT_PRIMARY,
        height=10,
        relief='solid',
        borderwidth=1,
        padx=10,
        pady=10
    )
    txt_outStr.grid(row=0, column=0, sticky='nsew')
    
    txt_outStr1 = tk.Text(
        ang_text_frame,
        wrap=tk.WORD,
        font=('Consolas', 10),
        fg=TEXT_PRIMARY,
        bg=WHITE,
        insertbackground=TEXT_PRIMARY,
        height=10,
        relief='solid',
        borderwidth=1,
        padx=10,
        pady=10
    )
    txt_outStr1.grid(row=0, column=0, sticky='nsew')

    # Add modern scrollbars
    rot_scrollbar = ttk.Scrollbar(rot_text_frame, orient='vertical', command=txt_outStr.yview)
    rot_scrollbar.grid(row=0, column=1, sticky='ns')
    txt_outStr.configure(yscrollcommand=rot_scrollbar.set)
    
    ang_scrollbar = ttk.Scrollbar(ang_text_frame, orient='vertical', command=txt_outStr1.yview)
    ang_scrollbar.grid(row=0, column=1, sticky='ns')
    txt_outStr1.configure(yscrollcommand=ang_scrollbar.set)

    # Configure text frame grids
    for frame in (rot_text_frame, ang_text_frame):
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    # Initialize loggers
    text_logger = TextLogger(txt_outStr)
    text_logger1 = TextLogger(txt_outStr1)

    # Load stored data or set defaults
    rot_axis_value = stored_data.get("axis_name", "X")
    rot_start_value = stored_data.get("start_position", 0)
    rot_travel_value = stored_data.get("travel", 360)
    rot_step_value = stored_data.get("step_size", 15)
    rot_stent_value = stored_data.get("stent", '')
    rot_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    rot_st_value = stored_data.get("stage_serial_number", '"Stage Serial Number"')
    rot_op_value = stored_data.get("operator", '"Your Initials"')
    rot_part_value = stored_data.get("part_number", '"Part Number"')
    rot_temp_value = stored_data.get("temp", 20)
    rot_comm_value = stored_data.get("comments", "")
    rot_col_value = stored_data.get("col_axis", '')

    # Section headers with modern styling
    section_font = font.Font(family="Segoe UI", size=9, weight="bold")
    section_style = {
        "bg": BACKGROUND,
        "fg": TEXT_SECONDARY,
        "font": section_font,
        "pady": 5
    }

    # Configure input frames with proper row indices
    for input_frame in (rot_input_frame, ang_input_frame):
        # Configure columns to be equal width
        for i in range(4):
            input_frame.grid_columnconfigure(i, weight=1, uniform='column')
            
        input_frame.h1_row = 0        # First separator
        input_frame.config_label_row = 1  # "CONFIGURATION" header
        input_frame.test_row = 2      # Select Test Type
        input_frame.h2_row = 3        # Second separator
        input_frame.params_label_row = 4  # "TEST PARAMETERS" header
        input_frame.axis_row = 5      # Axis Name
        input_frame.travel_row = 6    # Total Travel
        input_frame.step_row = 7      # Step Size
        input_frame.units_row = 8     # Units, Stent, and Calibrated
        input_frame.drive_row = 9     # Controller and Collimator Axis
        input_frame.h3_row = 10       # Third separator
        input_frame.doc_label_row = 11  # "DOCUMENTATION" header
        input_frame.sys_row = 12      # System Serial Number
        input_frame.job_row = 13      # Stage Serial Number
        input_frame.stage_row = 14    # Stage Part Number
        input_frame.op_row = 15       # Operator
        input_frame.temp_row = 16     # Temperature
        input_frame.comm_row = 17     # Comments
        input_frame.h4_row = 18       # Fourth separator
        input_frame.run_row = 19      # Run/Import buttons

        # Configure rows with proper spacing
        input_frame.rowconfigure(list(range(20)), weight=1, minsize=25)  # Reduced from 30

        # Create horizontal separators with modern styling
        for row in [input_frame.h1_row, input_frame.h2_row, input_frame.h3_row, input_frame.h4_row]:
            separator = tk.Frame(
                input_frame,
                height=1,
                bg=BORDER,  # Match the border color
                bd=0,
                highlightthickness=0
            )
            separator.grid(row=row, column=0, columnspan=4, sticky='ew', padx=10, pady=10)
            separator.grid_propagate(False)  # Maintain the height

        # Add section headers
        lbl_config = tk.Label(master=input_frame, text="CONFIGURATION", **section_style)
        lbl_config.grid(row=input_frame.config_label_row, column=0, columnspan=3, sticky='w', padx=10)

        lbl_params = tk.Label(master=input_frame, text="TEST PARAMETERS", **section_style)
        lbl_params.grid(row=input_frame.params_label_row, column=0, columnspan=3, sticky='w', padx=10)

        lbl_doc = tk.Label(master=input_frame, text="DOCUMENTATION", **section_style)
        lbl_doc.grid(row=input_frame.doc_label_row, column=0, columnspan=3, sticky='w', padx=10)

    # Base styles that can be extended
    base_style = {
        "bg": BACKGROUND,
        "relief": "flat",
        "padx": 12,
        "pady": 6
    }
    
    # Main input field labels (bolder, darker)
    main_label_style = {
        **base_style,
        "fg": TEXT_PRIMARY,
        "font": ("Segoe UI Semibold", 10),  # Reduced from 11
        "anchor": "w"  # Left-align text
    }
    
    # Supporting field labels (regular weight, slightly lighter)
    supporting_label_style = {
        **base_style,
        "fg": "#252423",  # Match the dark gray
        "font": ("Segoe UI", 10),
        "anchor": "w"  # Left-align text
    }
    
    # Entry field configurations
    entry_style = {
        "relief": "solid",
        "borderwidth": 1,
        "highlightthickness": 1,
        "highlightbackground": BORDER,
        "highlightcolor": BORDER,
        "bg": BACKGROUND,
        "fg": TEXT_PRIMARY,
        "insertbackground": TEXT_PRIMARY
    }

    # Radio button style
    radio_style = {
        "bg": BACKGROUND,  # Match parent background
        "fg": TEXT_SECONDARY,
        "selectcolor": WHITE,
        "activebackground": BACKGROUND,
        "activeforeground": BLUE_PRIMARY,
        "font": ("Segoe UI Semibold", 10),
        "cursor": "hand2"
    }

    # Frame style for radio button groups
    style.configure('RadioFrame.TFrame',
                   background=BACKGROUND)  # Match parent background

    # Add input fields with modern styling to both frames
    for input_frame, is_rotary in [(rot_input_frame, True), (ang_input_frame, False)]:
        if is_rotary:
            # Test Type Selection and Collimator Axis (side by side in configuration)
            lbl_test = tk.Label(input_frame, text="Test Type:", **main_label_style)
            lbl_test.grid(row=input_frame.test_row, column=0, padx=5, pady=3, sticky='w')
            
            direction = tk.StringVar(value=0)
            uni_dir = tk.Radiobutton(
                input_frame,
                text="Unidirectional",
                variable=direction,
                value="uni",
                command=lambda: test_type_def('uni'),
                **radio_style
            )
            uni_dir.grid(row=input_frame.test_row, column=1, padx=5, pady=3)
            
            bi_dir = tk.Radiobutton(
                input_frame,
                text="Bidirectional",
                variable=direction,
                value="bi",
                command=lambda: test_type_def('bi'),
                **radio_style
            )
            bi_dir.grid(row=input_frame.test_row, column=2, padx=5, pady=3)

            # Axis Name and Starting Position (side by side)
            lbl_axis = tk.Label(input_frame, text="Axis Name:", **main_label_style)
            lbl_axis.grid(row=input_frame.axis_row, column=0, padx=5, pady=5, sticky='w')
            
            var_axis = tk.StringVar(value=rot_axis_value)
            ent_axis = ttk.Entry(input_frame, textvariable=var_axis, style='Modern.TEntry')
            ent_axis.grid(row=input_frame.axis_row, column=1, padx=5, pady=5, sticky='ew')

            lbl_st = tk.Label(input_frame, text="Starting Position (deg):", **main_label_style)
            lbl_st.grid(row=input_frame.axis_row, column=2, padx=5, pady=5, sticky='w')
            
            var_start = tk.DoubleVar(value=rot_start_value)
            ent_start_pos = ttk.Entry(input_frame, textvariable=var_start, style='Modern.TEntry')
            ent_start_pos.grid(row=input_frame.axis_row, column=3, padx=5, pady=5, sticky='ew')

            # Total Travel and Step Size (side by side)
            lbl_travel = tk.Label(input_frame, text="Total Travel:", **main_label_style)
            lbl_travel.grid(row=input_frame.travel_row, column=0, padx=5, pady=5, sticky='w')
            
            var_travel = tk.DoubleVar(value=rot_travel_value)
            ent_travel = ttk.Entry(input_frame, textvariable=var_travel, style='Modern.TEntry')
            ent_travel.grid(row=input_frame.travel_row, column=1, padx=5, pady=5, sticky='ew')

            lbl_step = tk.Label(input_frame, text="Step Size:", **main_label_style)
            lbl_step.grid(row=input_frame.travel_row, column=2, padx=5, pady=5, sticky='w')
            
            var_step = tk.DoubleVar(value=rot_step_value)
            ent_step = ttk.Entry(input_frame, textvariable=var_step, style='Modern.TEntry')
            ent_step.grid(row=input_frame.travel_row, column=3, padx=5, pady=5, sticky='ew')

            # Units and Stent Diameter
            lbl_units = tk.Label(input_frame, text="Units:", **main_label_style)
            lbl_units.grid(row=input_frame.units_row, column=0, padx=5, pady=2, sticky='w')
            
            global unit_var
            unit_var = tk.StringVar(value='deg')
            
            def on_unit_change(*args):
                unit_def()
                # Enable/disable stent diameter based on units
                if unit_var.get() == 'deg':
                    ent_stent.configure(state=tk.DISABLED)
                else:
                    ent_stent.configure(state=tk.NORMAL)
            
            unit_var.trace_add('write', on_unit_change)
            
            units_frame = ttk.Frame(input_frame, style='RadioFrame.TFrame')
            units_frame.grid(row=input_frame.units_row, column=1, sticky='w')
            
            for i, (text, value) in enumerate([("deg", 'deg'), ("mm", 'mm'), ("in", 'in')]):
                ttk.Radiobutton(
                    units_frame,
                    text=text,
                    variable=unit_var,
                    value=value,
                    command=unit_def,
                    style='Modern.TRadiobutton'
                ).grid(row=0, column=i, padx=2)

            lbl_stent = tk.Label(input_frame, text="Stent Diameter (mm):", **main_label_style)
            lbl_stent.grid(row=input_frame.units_row, column=2, padx=5, pady=2, sticky='w')
            
            var_stent = tk.StringVar(value=rot_stent_value)
            ent_stent = ttk.Entry(input_frame, textvariable=var_stent, state=tk.DISABLED, width=8, style='Modern.TEntry')
            ent_stent.grid(row=input_frame.units_row, column=3, padx=5, pady=2, sticky='w')

            # Controller Selection and Collimator Axis
            lbl_drive = tk.Label(input_frame, text="Controller:", **main_label_style)
            lbl_drive.grid(row=input_frame.drive_row, column=0, padx=5, pady=2, sticky='w')
            
            global drive_var
            drive_var = tk.StringVar(value='USB')
            
            drive_frame = ttk.Frame(input_frame, style='RadioFrame.TFrame')
            drive_frame.grid(row=input_frame.drive_row, column=1, sticky='w')
            
            cbx_a1 = ttk.Radiobutton(
                drive_frame,
                text="A1",
                variable=drive_var,
                value='A1',
                command=drive_def,
                style='Modern.TRadiobutton'
            )
            cbx_a1.grid(row=0, column=0, padx=2)
            
            cbx_other = ttk.Radiobutton(
                drive_frame,
                text="A3200",
                variable=drive_var,
                value='USB',
                command=drive_def,
                style='Modern.TRadiobutton'
            )
            cbx_other.grid(row=0, column=1, padx=2)

            lbl_col = tk.Label(input_frame, text="Collimator Axis:", **main_label_style)
            lbl_col.grid(row=input_frame.drive_row, column=2, padx=5, pady=2, sticky='w')
            
            var_col = tk.StringVar(value=rot_col_value)
            col_options = ['X', 'Y']
            col_menu = ttk.OptionMenu(input_frame, var_col, col_options[0], *col_options, style='Modern.TMenubutton')
            col_menu.grid(row=input_frame.drive_row, column=3, padx=5, pady=2, sticky='w')
            col_menu.configure(width=3)

            # Documentation fields with adjusted widths and two-column layout
            var_sys_serial = tk.StringVar(value=rot_sys_value)
            ent_sys_serial = ttk.Entry(input_frame, textvariable=var_sys_serial, width=20, style='Modern.TEntry')

            var_st_serial = tk.StringVar(value=rot_st_value)
            ent_st_serial = ttk.Entry(input_frame, textvariable=var_st_serial, width=20, style='Modern.TEntry')

            var_stage = tk.StringVar(value=rot_part_value)
            ent_stage = ttk.Entry(input_frame, textvariable=var_stage, width=20, style='Modern.TEntry')

            var_op = tk.StringVar(value=rot_op_value)
            ent_op = ttk.Entry(input_frame, textvariable=var_op, width=20, style='Modern.TEntry')

            var_temp = tk.DoubleVar(value=rot_temp_value)  # Define temperature variable here
            ent_temp = ttk.Entry(input_frame, textvariable=var_temp, width=8, style='Modern.TEntry')

            var_comm = tk.StringVar(value=rot_comm_value)
            ent_comm = ttk.Entry(input_frame, textvariable=var_comm, width=40, style='Modern.TEntry')

            # Add documentation fields to grid in two columns
            # Left column
            lbl_sys = tk.Label(input_frame, text="System Serial Number:", **main_label_style)
            lbl_sys.grid(row=input_frame.sys_row, column=0, padx=5, pady=2, sticky='w')
            ent_sys_serial.grid(row=input_frame.sys_row, column=1, padx=5, pady=2, sticky='w')

            lbl_stage = tk.Label(input_frame, text="Stage Part Number:", **main_label_style)
            lbl_stage.grid(row=input_frame.stage_row, column=0, padx=5, pady=2, sticky='w')
            ent_stage.grid(row=input_frame.stage_row, column=1, padx=5, pady=2, sticky='w')

            # Right column
            lbl_st = tk.Label(input_frame, text="Stage Serial Number:", **main_label_style)
            lbl_st.grid(row=input_frame.sys_row, column=2, padx=5, pady=2, sticky='w')
            ent_st_serial.grid(row=input_frame.sys_row, column=3, padx=5, pady=2, sticky='w')

            lbl_op = tk.Label(input_frame, text="Operator:", **main_label_style)
            lbl_op.grid(row=input_frame.stage_row, column=2, padx=5, pady=2, sticky='w')
            ent_op.grid(row=input_frame.stage_row, column=3, padx=5, pady=2, sticky='w')

            # Temperature and Calibrated
            lbl_temp = tk.Label(input_frame, text="Temperature (°C):", **main_label_style)
            lbl_temp.grid(row=input_frame.temp_row, column=0, padx=5, pady=2, sticky='w')
            ent_temp.grid(row=input_frame.temp_row, column=1, padx=5, pady=2, sticky='w')  # Just grid the existing entry

            var_cal = tk.IntVar(value=0)
            cbx_cal = ttk.Checkbutton(
                input_frame,
                text="Calibrated",
                variable=var_cal,
                state=tk.NORMAL,
                style='Modern.TCheckbutton'
            )
            cbx_cal.grid(row=input_frame.temp_row, column=2, padx=5, pady=2, sticky='w')

            # Comments spans both columns
            lbl_comm = tk.Label(input_frame, text="Comments:", **main_label_style)
            lbl_comm.grid(row=input_frame.comm_row, column=0, padx=5, pady=2, sticky='w')
            ent_comm.grid(row=input_frame.comm_row, column=1, columnspan=3, padx=5, pady=2, sticky='ew')

            def on_controller_change(*args):
                drive_def()
                # Enable/disable collimator axis and calibrated based on controller
                if drive_var.get() == 'A1':
                    col_menu.configure(state=tk.DISABLED)
                    cbx_cal.configure(state=tk.DISABLED)
                else:
                    col_menu.configure(state=tk.NORMAL)
                    cbx_cal.configure(state=tk.NORMAL)
            
            drive_var.trace_add('write', on_controller_change)

            # Initial state setup
            on_unit_change()
            on_controller_change()

            # Adjust vertical padding for specific rows
            input_frame.rowconfigure(input_frame.travel_row, minsize=20)  # Reduced space after Total Travel row
            input_frame.rowconfigure(input_frame.units_row, minsize=20)  # Reduced space before Units row

            # Action buttons row with more vertical space
            button_frame = ttk.Frame(input_frame, style='Card.TFrame')
            button_frame.grid(row=input_frame.run_row, column=0, columnspan=4, sticky='ew', padx=5, pady=(15, 25))  # Increased padding
            button_frame.columnconfigure(0, weight=1)
            button_frame.columnconfigure(1, weight=1)
            button_frame.columnconfigure(2, weight=1)

            btn_run = ttk.Button(
                button_frame,
                text="Run Test",
                command=lambda frame=input_frame: start_test(frame),
                style='Primary.TButton'
            )
            btn_run.grid(row=0, column=0, padx=5, pady=(5, 10), sticky='ew')  # Added bottom padding
            
            btn_import = ttk.Button(
                button_frame,
                text="Import Data",
                command=lambda frame=input_frame: import_data(frame),
                style='Secondary.TButton'
            )
            btn_import.grid(row=0, column=1, padx=5, pady=(5, 10), sticky='ew')  # Added bottom padding

            btn_open_plot = ttk.Button(
                button_frame,
                text="Open Plot",
                command=open_rotary_Plot,
                style='Secondary.TButton'
            )
            btn_open_plot.grid(row=0, column=2, padx=5, pady=(5, 10), sticky='ew')  # Added bottom padding

    window.mainloop()

if __name__ == '__main__':
    UI()
    
