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
test_type = 'None'
units = 'deg'
drive = 'None'
is_cal = 0
window = None

# Add global variables for UI controls
unit_var = None
col_axis_var = None
drive_var = None
direction = None
rot_plot_manager = None
txt_outStr = None
plot_manager = None

# Add Tkinter variables
var_axis = None
var_step = None
var_travel = None
var_start = None
var_temp = None
var_sys_serial = None
var_st_serial = None
var_comm = None
var_stage = None
var_op = None
var_stent = None
var_cal = None
var_col = None

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

def cleanup_resources(rot_cal=None):
    """
    Cleans up resources such as threads, connections, and resets global states.
    """
    global plot_thread, test_thread, server_thread, is_plot_running, ani, canvas, fig
    is_plot_running = False
    
    if 'ani' in globals() and ani:
        ani.event_source.stop()
        ani = None

    if 'plot_thread' in globals() and plot_thread and plot_thread.is_alive():
        plot_thread.join(timeout=1)
    plot_thread = None

    if test_thread and test_thread.is_alive():
        try:
            test_thread.join(timeout=1)
        except RuntimeError:
            pass
    test_thread = None
    
    if server_thread and server_thread.is_alive():
        server_thread.join(timeout=1)
    server_thread = None

    # Close client socket if it exists
    if clientsocket:
        clientsocket.close()
    
    # Clean up rot_cal specific resources
    if rot_cal:
        del rot_cal
    
    gc.collect()

def start_test(input_frame):
    """Start button callback"""
    try:
        # Add global declarations
        global var_axis, var_step, var_travel, var_start, var_temp
        global var_sys_serial, var_st_serial, var_comm, var_stage, var_op
        global var_stent, var_cal, var_col, test_type, units, drive
        global controller, test_thread, server_thread
        # Disable run button
        for widget in input_frame.winfo_children():
            if isinstance(widget, ttk.Button) and widget['text'] == 'Run Test':
                widget.config(state=tk.DISABLED)
                break
        
        # Validate test direction
        if test_type not in ['Unidirectional', 'Bidirectional']:
            raise ValueError("Please select a test direction (Unidirectional or Bidirectional)")
        
        # Get and validate values from Tkinter variables
        try:
            axis = str(var_axis.get()).strip()
            if not axis:
                raise ValueError("Axis Name is required")
                
            step_size = float(var_step.get())
            if step_size <= 0:
                raise ValueError("Step Size must be greater than 0")
                
            travel = float(var_travel.get())
            if travel <= 0:
                raise ValueError("Total Travel must be greater than 0")
                
            start_pos = float(var_start.get())
            temp = float(var_temp.get())
            sys_serial = str(var_sys_serial.get()).strip()
            st_serial = str(var_st_serial.get()).strip()
            comments = str(var_comm.get()).strip()
            stage = str(var_stage.get()).strip()
            op = str(var_op.get()).strip()
            
            # Validate required fields
            if not all([sys_serial, st_serial, stage, op]):
                raise ValueError("All documentation fields are required")
            
            # Get stent diameter if available
            if unit_var.get() != 'deg':
                dia = float(var_stent.get())
                if dia <= 0:
                    raise ValueError("Stent Diameter must be greater than 0")
            else:
                dia = 0
                
        except ValueError as e:
            raise ValueError(f"Invalid input: {str(e)}")
            
        # Default values
        num_readings = 10  # Default number of readings
        dwell = 0.1  # Default dwell time
        
        # Handle Automation1 controller connection if needed
        if drive == 'Automation1':
            try:
                controller = a1.Controller.connect()
                controller.start()
            except:
                connection_type = controller_def()
                if connection_type == 'yes':
                    try:
                        controller = a1.Controller.connect_usb()
                        controller.start()
                    except:
                        messagebox.showerror('Connection Error', 'Check connections and try again')
                        return
                else:
                    messagebox.showerror('Update Software', 'Update Hyperwire firmware and try again')
                    return

            # Get connected axes
            connected_axes = {}
            non_virtual_axes = []
            number_of_axes = controller.runtime.parameters.axes.count

            axis_range = range(0, 32) if number_of_axes > 12 else range(0, 11)
            
            for axis_index in axis_range:
                status_item_configuration = a1.StatusItemConfiguration()
                status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
                result = controller.runtime.status.get_status_items(status_item_configuration)
                axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
                
                if (axis_status & 1 << 13) > 0:
                    connected_axes[controller.runtime.parameters.axes[axis_index].identification.axisname.value] = axis_index

            for key, value in connected_axes.items():
                non_virtual_axes.append(key)
                
            if len(non_virtual_axes) == 0:
                try:
                    controller = a1.Controller.connect_usb()
                except:
                    messagebox.showerror('No Device', 'No Devices Present. Check Connections.')
                    return

            # Clean up temporary objects
            del connected_axes, non_virtual_axes, status_item_configuration, result

        # Initialize plot
        plot_manager = rot_plot_manager
        plot_manager.setup_plot(axis, units=units)
        
        # Set up data callback
        def on_data_update(positions, measurements, reverse_data=None, axis_num=None):
            plot_manager.update_plot(positions, measurements, reverse_data, axis_num, units=units)
        
        # Create and run test instance
        test_instance = rotary_cal(
            axis=axis,
            num_readings=num_readings,
            dwell=dwell,
            step_size=step_size,
            travel=travel,
            units=units,
            dia=dia,
            test_type=test_type,
            sys_serial=sys_serial,
            st_serial=st_serial,
            comments=comments,
            temp=temp,
            start_pos=start_pos,
            drive=drive,
            stage_type=stage,
            oper=op,
            text_widget=txt_outStr,
            window=window,
            on_data_update=on_data_update,
            is_cal=var_cal.get(),
            col_axis=var_col.get()
        )
        
        # Run the test based on controller type
        if drive == 'Automation1':
            test_instance.a1_test(controller)
        else:
            test_instance.test()
            
        # Cleanup after test
        if controller:
            controller.disconnect()
            controller = None
            
        cleanup_resources(test_instance)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        messagebox.showerror("Error", f"Failed to start test: {str(e)}\n\nDetails:\n{error_details}")
        # Re-enable run button
        for widget in input_frame.winfo_children():
            if isinstance(widget, ttk.Button) and widget['text'] == 'Run Test':
                widget.config(state=tk.NORMAL)
                break

def import_data(input_frame):
    """Import data from a file."""
    try:
        global var_axis, var_step, var_travel, var_start, var_temp
        global var_sys_serial, var_st_serial, var_comm, var_stage, var_op
        global var_stent, var_cal, var_col, test_type, units, drive
        global controller, test_thread, server_thread

        # Validate test direction
        if test_type not in ['Unidirectional', 'Bidirectional']:
            raise ValueError("Please select a test direction (Unidirectional or Bidirectional)")
        
        # Get and validate values from Tkinter variables
        try:
            axis = str(var_axis.get()).strip()
            if not axis:
                raise ValueError("Axis Name is required")
                
            step_size = float(var_step.get())
            if step_size <= 0:
                raise ValueError("Step Size must be greater than 0")
                
            travel = float(var_travel.get())
            if travel <= 0:
                raise ValueError("Total Travel must be greater than 0")
                
            start_pos = float(var_start.get())
            temp = float(var_temp.get())
            sys_serial = str(var_sys_serial.get()).strip()
            st_serial = str(var_st_serial.get()).strip()
            comments = str(var_comm.get()).strip()
            stage = str(var_stage.get()).strip()
            op = str(var_op.get()).strip()
            
            # Validate required fields
            if not all([sys_serial, st_serial, stage, op]):
                raise ValueError("All documentation fields are required")
            
            # Get stent diameter if available
            if unit_var.get() != 'deg':
                dia = float(var_stent.get())
                if dia <= 0:
                    raise ValueError("Stent Diameter must be greater than 0")
            else:
                dia = 0
                
        except ValueError as e:
            raise ValueError(f"Invalid input: {str(e)}")
            
        # Default values
        num_readings = 10  # Default number of readings
        dwell = 0.1  # Default dwell time

        # Get test parameters
        axis = str(var_axis.get())
        step_size = float(var_step.get())
        travel = float(var_travel.get())
        st_serial = str(var_st_serial.get())
        comments = str(var_comm.get())
        stage = str(var_stage.get())
        op = str(var_op.get())
        
        test_class = rotary_cal
        text_widget = txt_outStr
        
        # Create test instance
        test_instance = test_class(
            axis=axis,
            num_readings=num_readings,
            dwell=dwell,
            step_size=step_size,
            travel=travel,
            units=units,
            dia=dia,
            test_type=test_type,
            sys_serial=sys_serial,
            st_serial=st_serial,
            comments=comments,
            temp=temp,
            start_pos=start_pos,
            drive=drive,
            stage_type=stage,
            oper=op,
            text_widget=txt_outStr,
            window=window,
            is_cal=var_cal.get(),
            col_axis=var_col.get()
        )
        
        # Import the data
        test_instance.import_data()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import data: {str(e)}")

def open_rotary_Plot():
    sys.stdout = TextLogger(txt_outStr)
    axis = var_axis.get()
    sys_serial = var_sys_serial.get()

    start_path = ('O:/')
    folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(start_path) for dir_name in dirs if str(sys_serial[0:6]) in dir_name), None)
    pdf_file_path = folder_path + '/Customer Files/Plots'

    if os.path.exists(pdf_file_path):
        try:
            output_file = str(sys_serial + '-' + axis + "_Accuracy.pdf")
            pdf = pdf_file_path + '/' + output_file
            os.startfile(pdf)
        except:
            pass
        try:
            output_file = str(sys_serial + '-' + axis + "_Verification.pdf")
            pdf = pdf_file_path + '/' + output_file
            os.startfile(pdf)
        except:
            pass
    else:
        print(f"File '{pdf_file_path}' does not exist.")

def UI():
    global window, plot_manager, test_type, units, drive, is_cal, rot_plot_manager, txt_outStr
    global var_axis, var_step, var_travel, var_start, var_temp, var_sys_serial, var_st_serial, var_comm, var_stage, var_op, var_stent, var_cal, var_col
    global unit_var, col_axis_var, drive_var, direction

    # Initialize global variables
    test_type = 'None'
    units = 'deg'
    drive = 'None'
    is_cal = 0
    plot_manager = None
    rot_plot_manager = None
    txt_outStr = None
    
    # Load stored user inputs
    stored_data = load_user_inputs()
    
    # Initialize Tkinter window with Automation1 styling
    window = tk.Tk()
    window.title("Rotary Testing")
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
    
    style.configure('Button.TFrame',
                   background=BACKGROUND,
                   )
    
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

    # Create main frame
    main_frame = ttk.Frame(window, style='Card.TFrame')
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(0, weight=0)
    main_frame.grid_columnconfigure(1, weight=1)

    # Create input frame
    input_frame_width = 850
    input_frame_height = 800

    input_frame = ttk.Frame(
        main_frame,
        padding="10 10 10 10",
        style='Card.TFrame',
        width=input_frame_width,
        height=input_frame_height
    )
    input_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

    # Create plot frame
    plot_frame_width = 900
    plot_frame = ttk.Frame(main_frame, padding="10 10 10 10", style='Card.TFrame', width=plot_frame_width)
    plot_frame.grid(row=0, column=1, rowspan=2, sticky='nsew', padx=10, pady=10)

    # Configure plot frame
    plot_frame.grid_rowconfigure(0, weight=1)
    plot_frame.grid_columnconfigure(0, weight=1)
    plot_frame.grid_propagate(False)

    # Initialize plot manager
    rot_plot_manager = PlotManager(window, plot_frame, plot_type='rotary')

    # Create text output frame
    text_frame = ttk.Frame(main_frame, padding="10 10 10 10", style='Card.TFrame')
    text_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

    # Configure text widget
    txt_outStr = tk.Text(
        text_frame,
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

    # Add modern scrollbar
    scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=txt_outStr.yview)
    scrollbar.grid(row=0, column=1, sticky='ns')
    txt_outStr.configure(yscrollcommand=scrollbar.set)

    # Configure text frame grid
    text_frame.grid_rowconfigure(0, weight=1)
    text_frame.grid_columnconfigure(0, weight=1)

    # Initialize logger
    text_logger = TextLogger(txt_outStr)

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
    for input_frame in (input_frame,):
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

    def test_type_def():
        global test_type
        if direction.get() == "uni":
            test_type = 'Unidirectional'
        elif direction.get() == "bi":
            test_type = 'Bidirectional'
        else:
            test_type = 'None'

    def unit_def():
        global units
        if unit_var.get() == 'deg':
            var_stent.set('None')
            units = 'deg'
            ent_stent["state"] = tk.DISABLED
        elif unit_var.get() == 'mm':
            units = 'mm'
            ent_stent["state"] = tk.NORMAL
        elif unit_var.get() == 'in':
            units = 'in'
            ent_stent["state"] = tk.NORMAL
        else:
            units = 'None'
            ent_stent["state"] = tk.DISABLED

    def drive_def():
        global drive, is_cal
        if drive_var.get() == 'A1':
            cbx_cal["state"] = tk.DISABLED
            col_menu["state"] = tk.DISABLED
            var_cal.set(0)
            var_cal.set(0)
            is_cal = 0
            drive = 'Automation1'
        elif drive_var.get() == 'Other':
            cbx_cal["state"] = tk.NORMAL
            col_menu["state"] = tk.NORMAL
            drive = 'Other'
            if var_cal.get() == 1:
                is_cal = 1
            else:
                is_cal = 0
        else:
            drive = 'None'

    def cal_def():
        global is_cal
        if var_cal.get() == 1:
            is_cal = 1
        else:
            is_cal = 0

    # Frame style for radio button groups
    style.configure('RadioFrame.TFrame',
                   background=BACKGROUND)  # Match parent background

    # Add input fields with modern styling to both frames
    #for input_frame, is_rotary in [(input_frame, True)]:
    # Test Type Selection
    lbl_test = tk.Label(input_frame, text="Test Type:", **main_label_style)
    lbl_test.grid(row=input_frame.test_row, column=0, padx=5, pady=3, sticky='w')
    
    direction = tk.StringVar(value=0)
    uni_dir = ttk.Radiobutton(
        input_frame,
        text="Unidirectional",
        variable=direction,
        value="uni",
        command=test_type_def,
        style='Modern.TRadiobutton'
    )
    uni_dir.grid(row=input_frame.test_row, column=1, padx=5, pady=3)
    
    bi_dir = ttk.Radiobutton(
        input_frame,
        text="Bidirectional",
        variable=direction,
        value="bi",
        command=test_type_def,
        style='Modern.TRadiobutton'
    )
    bi_dir.grid(row=input_frame.test_row, column=2, padx=5, pady=3)

    # Axis Name and Starting Position
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

    # Total Travel and Step Size
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

    # Units Selection
    lbl_units = tk.Label(input_frame, text="Units:", **main_label_style)
    lbl_units.grid(row=input_frame.units_row, column=0, padx=5, pady=2, sticky='w')
    
    unit_var = tk.StringVar(value=0)
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

    # Stent Diameter
    lbl_stent = tk.Label(input_frame, text="Stent Diameter (mm):", **main_label_style)
    lbl_stent.grid(row=input_frame.units_row, column=2, padx=5, pady=2, sticky='w')
    
    var_stent = tk.StringVar(value=rot_stent_value)
    ent_stent = ttk.Entry(input_frame, textvariable=var_stent, state=tk.DISABLED, style='Modern.TEntry')
    ent_stent.grid(row=input_frame.units_row, column=3, padx=5, pady=2, sticky='w')

    # Controller Selection
    lbl_drive = tk.Label(input_frame, text="Controller:", **main_label_style)
    lbl_drive.grid(row=input_frame.drive_row, column=0, padx=5, pady=2, sticky='w')
    
    drive_var = tk.StringVar(value=0)
    drive_frame = ttk.Frame(input_frame, style='RadioFrame.TFrame')
    drive_frame.grid(row=input_frame.drive_row, column=1, sticky='w')
    
    ttk.Radiobutton(
        drive_frame,
        text="A1",
        variable=drive_var,
        value='A1',
        command=drive_def,
        style='Modern.TRadiobutton'
    ).grid(row=0, column=0, padx=2)
    
    ttk.Radiobutton(
        drive_frame,
        text="Other",
        variable=drive_var,
        value='Other',
        command=drive_def,
        style='Modern.TRadiobutton'
    ).grid(row=0, column=1, padx=2)

    # Collimator Axis
    lbl_col = tk.Label(input_frame, text="Collimator Axis:", **main_label_style)
    lbl_col.grid(row=input_frame.drive_row, column=2, padx=5, pady=2, sticky='w')
    
    var_col = tk.StringVar(value=rot_col_value)
    col_menu = ttk.OptionMenu(input_frame, var_col, rot_col_value, 'X', 'Y', style='Modern.TMenubutton')
    col_menu.grid(row=input_frame.drive_row, column=3, padx=5, pady=2, sticky='w')
    col_menu.configure(width=3)

    # Calibration Checkbox
    var_cal = tk.IntVar(value=0)
    cbx_cal = ttk.Checkbutton(
        input_frame,
        text="Calibrated",
        variable=var_cal,
        command=cal_def,
        style='Modern.TCheckbutton'
    )
    cbx_cal.grid(row=input_frame.temp_row, column=2, padx=5, pady=2, sticky='w')

    # Documentation fields
    var_sys_serial = tk.StringVar(value=rot_sys_value)
    var_st_serial = tk.StringVar(value=rot_st_value)
    var_stage = tk.StringVar(value=rot_part_value)
    var_op = tk.StringVar(value=rot_op_value)
    var_temp = tk.DoubleVar(value=rot_temp_value)
    var_comm = tk.StringVar(value=rot_comm_value)

    # Left Column
    # System Serial Number
    lbl_sys = tk.Label(input_frame, text="System Serial Number:", **main_label_style)
    lbl_sys.grid(row=input_frame.sys_row, column=0, padx=5, pady=2, sticky='w')
    ent_sys_serial = ttk.Entry(input_frame, textvariable=var_sys_serial, width=25, style='Modern.TEntry')
    ent_sys_serial.grid(row=input_frame.sys_row, column=1, padx=5, pady=2, sticky='w')

    # Stage Part Number
    lbl_stage = tk.Label(input_frame, text="Stage Part Number:", **main_label_style)
    lbl_stage.grid(row=input_frame.stage_row, column=0, padx=5, pady=2, sticky='w')
    ent_stage = ttk.Entry(input_frame, textvariable=var_stage, width=25, style='Modern.TEntry')
    ent_stage.grid(row=input_frame.stage_row, column=1, padx=5, pady=2, sticky='w')

    # Temperature
    lbl_temp = tk.Label(input_frame, text="Temperature (°C):", **main_label_style)
    lbl_temp.grid(row=input_frame.temp_row, column=0, padx=5, pady=2, sticky='w')
    ent_temp = ttk.Entry(input_frame, textvariable=var_temp, width=8, style='Modern.TEntry')
    ent_temp.grid(row=input_frame.temp_row, column=1, padx=5, pady=2, sticky='w')

    # Right Column
    # Stage Serial Number
    lbl_st = tk.Label(input_frame, text="Stage Serial Number:", **main_label_style)
    lbl_st.grid(row=input_frame.sys_row, column=2, padx=5, pady=2, sticky='w')
    ent_st_serial = ttk.Entry(input_frame, textvariable=var_st_serial, width=25, style='Modern.TEntry')
    ent_st_serial.grid(row=input_frame.sys_row, column=3, padx=5, pady=2, sticky='w')

    # Operator
    lbl_op = tk.Label(input_frame, text="Operator:", **main_label_style)
    lbl_op.grid(row=input_frame.stage_row, column=2, padx=5, pady=2, sticky='w')
    ent_op = ttk.Entry(input_frame, textvariable=var_op, width=25, style='Modern.TEntry')
    ent_op.grid(row=input_frame.stage_row, column=3, padx=5, pady=2, sticky='w')

    # Comments (spans both columns)
    lbl_comments = tk.Label(input_frame, text="Comments:", **main_label_style)
    lbl_comments.grid(row=input_frame.comm_row, column=0, padx=5, pady=2, sticky='w')
    ent_comments = ttk.Entry(input_frame, textvariable=var_comm, width=80, style='Modern.TEntry')
    ent_comments.grid(row=input_frame.comm_row, column=1, columnspan=3, padx=5, pady=2, sticky='w')

    # Update other entry field widths
    ent_axis.configure(width=25)
    ent_start_pos.configure(width=25)
    ent_travel.configure(width=25)
    ent_step.configure(width=25)
    ent_stent.configure(width=25)

    # Action buttons
    button_frame = ttk.Frame(input_frame, style='Button.TFrame')
    button_frame.grid(row=input_frame.run_row, column=0, columnspan=4, sticky='ew', padx=5, pady=(15, 25))
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)
    button_frame.columnconfigure(2, weight=1)

    btn_run = ttk.Button(
        button_frame,
        text="Run Test",
        command=lambda frame=input_frame: start_test(frame),
        style='Primary.TButton'
    )
    btn_run.grid(row=0, column=0, padx=5, pady=(5, 10), sticky='ew')
    
    btn_import = ttk.Button(
        button_frame,
        text="Import Data",
        command=lambda frame=input_frame: import_data(frame),
        style='Secondary.TButton'
    )
    btn_import.grid(row=0, column=1, padx=5, pady=(5, 10), sticky='ew')

    btn_open_plot = ttk.Button(
        button_frame,
        text="Open Plot",
        command=open_rotary_Plot,
        style='Secondary.TButton'
    )
    btn_open_plot.grid(row=0, column=2, padx=5, pady=(5, 10), sticky='ew')

    window.mainloop()

if __name__ == '__main__':
    UI()
    