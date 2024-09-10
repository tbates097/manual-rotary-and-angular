# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:03:56 2024

@author: tbates
"""

import os
import sys
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox,font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import threading
import automation1 as a1
from RotaryCalTest import rotary_cal
from AngularTest import angular
from Logger import TextLogger
import socket
import gc
import json
import queue

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
# Initialize global variables and states
# Create separate queues for forward and reverse data
forward_queue = queue.Queue()
reverse_queue = queue.Queue()
# Global lists to accumulate data
xforwarddata, yforwarddata = [], []
xreversedata, yreversedata = [], []
yrawforward, yrawreverse = [], []
clientsocket = None
plot_thread = None
server_ready_event = threading.Event()
test_thread = None
server_thread = None
controller = None
is_plot_running = False  # Ensure this is defined globally
ani = None
# Initialize plot line objects as None
forward_line = None
reverse_line = None

# JSON file path to store user inputs
USER_DATA_FILE = os.path.join(os.getcwd(), "user_data.json")

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
    ver.configure(bg='white')

    custom_font = font.Font(family="Times New Roman", size=12, weight="bold")

    label = tk.Label(ver, text="Are you trying to connect via USB?", bg='white', font=custom_font)
    label.grid(row=0, column=0, columnspan=2, padx=10, pady=5)

    def on_yes():
        ver.result = 'yes'
        ver.destroy()

    def on_no():
        ver.result = 'No'
        ver.destroy()

    button_ok = tk.Button(ver, text="Yes", width=10, height=2, command=on_yes)
    button_ok.grid(row=4, column=0, padx=10, pady=10)

    button_cancel = tk.Button(ver, text="No", width=10, height=2, command=on_no)
    button_cancel.grid(row=4, column=1, padx=10, pady=10)

    ver.resizable(False, False)

    ver.update_idletasks()  # Ensure that the window sizes correctly

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

def UI():
    global ani,ani1,ani2, window, ax, queue
    
    # Load stored user inputs
    stored_data = load_user_inputs()
    
    # Initialize Tkinter window
    window = tk.Tk()
    window.title("Rotary and Angular Testing")

    window.resizable(True, False)  # This code helps to disable windows from resizing

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    window_height = 900
    window_width = 1700

    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))

    window.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))

    interface = ttk.Notebook(window)
    interface.pack(fill='both', expand=True)

    # Create frames for each tab
    tab1 = ttk.Frame(interface, width=window_width, height=window_height)
    tab2 = ttk.Frame(interface, width=window_width, height=window_height)

    # Add tabs to the notebook
    interface.add(tab1, text='Rotary Cal')
    interface.add(tab2, text='Angular Testing')

    for tab in (tab1, tab2):
        # Configure columns and rows
        tab.columnconfigure([0, 1, 2, 3, 4, 5, 6], weight=1, minsize=700 / 4, uniform='column')
        tab.rowconfigure([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21], weight=1, minsize=1)

        # Define row indices
        df_row = 0
        h1_row = 1
        test_row = 2
        h2_row = 3
        axName_row = 4
        ll_row = 5
        ul_row = 6
        ts_row = 7
        filt_row = 8
        eq_row = 9
        eqa_row = 10
        h3_row = 11
        sn_row = 12
        stage_row = 13
        op_row = 14
        cv_row = 15
        ol_row = 16
        pm_row = 17
        col_row = 18
        h4_row = 19
        run_row = 20
        out_row = 21

        window.rowconfigure(out_row, minsize=4)

        # Create horizontal separators
        ttk.Separator(master=tab, orient='horizontal').grid(row=h1_row, column=0, columnspan=4, sticky='ew')
        ttk.Separator(master=tab, orient='horizontal').grid(row=h2_row, column=0, columnspan=4, sticky='ew')
        ttk.Separator(master=tab, orient='horizontal').grid(row=h3_row, column=0, columnspan=4, sticky='ew')
        ttk.Separator(master=tab, orient='horizontal').grid(row=h4_row, column=0, columnspan=4, sticky='ew')

        # Adjust column weights so the vertical separator aligns correctly
        tab.columnconfigure(3, weight=1)
        tab.columnconfigure(4, weight=1)
    
    # Add the vertical separator to the frame
    ttk.Separator(master=tab1, orient='vertical').grid(row=h1_row, column=4, rowspan=21, sticky='nsw', pady=(4, 0))
    # Add the vertical separator to the frame
    ttk.Separator(master=tab2, orient='vertical').grid(row=h1_row, column=4, rowspan=21, sticky='nsw', pady=(7, 0))
    
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
    
    # Load stored data or set defaults
    ang_axis_value = stored_data.get("axis_name", "X")
    ang_start_value = stored_data.get("start_position", 0)
    ang_travel_value = stored_data.get("travel", 100)
    ang_step_value = stored_data.get("step_size", 5)
    ang_controller_value = stored_data.get("controller", '')
    ang_units_value = stored_data.get("units", '')
    ang_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    ang_st_value = stored_data.get("stage_serial_number", '"Stage Serial Number"')
    ang_op_value = stored_data.get("operator", '"Your Initials"')
    ang_part_value = stored_data.get("part_number", '"Part Number"')
    ang_temp_value = stored_data.get("temp", 20)
    ang_comm_value = stored_data.get("comments", "")
    
    def start_rotarycaltest():
        """
        Starts the rotary calibration test. Initializes required data and disables the run button.
        """
        global yrawforward, yrawreverse, xforwarddata, xreversedata, yforwarddata, yreversedata, test_thread
        
        # Clear data
        yrawforward, yrawreverse = [], []
        xforwarddata, xreversedata = [], []
        yforwarddata, yreversedata = [], []
    
        # Disable the Run button during the test
        btn_run_rot.config(state=tk.DISABLED)
        
        # Start the server first
        start_server()
        
        # Start the plot thread
        start_plot_thread()
        
        # Check server readiness without blocking the GUI
        check_server_ready()

    def check_server_ready():
        """
        Checks if the server is ready without blocking the GUI.
        If the server is ready, starts the test thread.
        """
        if server_ready_event.is_set():
            # Start the test thread if the server is ready
            start_test_thread()
        else:
            # Re-check after 100ms
            window.after(100, check_server_ready)
    
    def start_test_thread():
        """
        Starts the test thread for running the rotary calibration test.
        """
        global test_thread
        test_thread = threading.Thread(target=run_rotarycaltest, daemon=True)
        test_thread.start()
    
    def start_plot_thread():
        """
        Starts a thread for handling live plot updates. Ensures that only one plot thread is running at a time.
        """
        global plot_thread, is_plot_running
        if not is_plot_running:
            is_plot_running = True
            plot_thread = threading.Thread(target=rotary_live_plot, daemon=True)
            plot_thread.start()
            
    def rotary_live_plot():
        """
        Function to handle live plotting. Sets up the plot, initializes the animation, and manages updates from a queue.
        """
        global ani, forward_line, reverse_line
    
        # Create figure and axis for the plot
        fig, ax = plt.subplots()
        ax.set_facecolor("white")
        ax.set_xlabel("Position", color='darkred')
        ax.set_ylabel("Accuracy", color='darkred')
        ax.set_title("Live Plot of Position vs Accuracy")
        
        # Initialize the line objects for forward and reverse data
        forward_line, = ax.plot([], [], 'b-o', label='Forward')
        reverse_line, = ax.plot([], [], 'r-x', label='Reverse')
    
        canvas = FigureCanvasTkAgg(fig, master=tab1)
        canvas.get_tk_widget().grid(row=0, column=4, rowspan=21, columnspan=3, padx=1, pady=(13, 0), sticky='nsew')
        ax.grid(False)
    
        # Add legend
        ax.legend()
    
        def update_plot(frame):
            """
            Update function for the animation. Fetches data from the queues and updates the plot.
            """
            # Get forward data from the queue
            if not forward_queue.empty():
                xforward, yforward = forward_queue.get()
                forward_line.set_data(xforward, yforward)  # Update line data
            
            # Get reverse data from the queue
            if not reverse_queue.empty():
                xreverse, yreverse = reverse_queue.get()
                reverse_line.set_data(xreverse, yreverse)  # Update line data
            
            # Set plot limits and redraw
            ax.relim()
            ax.autoscale_view()
            canvas.draw()
    
        # Initialize the animation
        ani = FuncAnimation(fig, update_plot, interval=100)
    
        def on_close(event):
            """
            Cleanup function to run when closing the plot.
            """
            global is_plot_running
            ani.event_source.stop()
            plt.close(fig)
            is_plot_running = False
    
        fig.canvas.mpl_connect('close_event', on_close)
    
    def start_server():
        """
        Starts a server socket to listen for incoming connections and handles data received from clients.
        """
        global clientsocket, server_thread
        
        def handle_client(clientsocket):
            """
            Handles incoming data from the client socket and categorizes it into forward or reverse data.
            """
            global yrawforward, yrawreverse, xforwarddata, xreversedata, yforwarddata, yreversedata
            
            while True:
                try:
                    data = clientsocket.recv(1024)
                    if not data:
                        break
                    
                    data = data.decode('utf-8').split(',')
                    forward_data = None
                    reverse_data = None
                    
                    # Extract and categorize data as forward or reverse
                    for item in data:
                        if "forward_fbk" in item:
                            forward_fbk = item.split(":")[1].strip()
                            x = float(forward_fbk)
                            xforwarddata.append(x)
                        elif "forward_col" in item:
                            forward_data = item.split(":")[1].strip()
                            y = float(forward_data)
                            yrawforward.append(y)
                            plot_mean = np.mean(yrawforward)
                            yforwarddata = [i - plot_mean for i in yrawforward]
        
                            # Put forward data in the forward queue
                            forward_queue.put((xforwarddata.copy(), yforwarddata.copy()))  # Use .copy() to keep the current state
        
                        elif "reverse_fbk" in item:
                            reverse_fbk = item.split(":")[1].strip()
                            x = float(reverse_fbk)
                            xreversedata.append(x)
                        elif "reverse_col" in item:
                            reverse_data = item.split(":")[1].strip()
                            y = float(reverse_data)
                            yrawreverse.append(y)
                            plot_mean = np.mean(yrawreverse)
                            yreversedata = [i - plot_mean for i in yrawreverse]
        
                            # Put reverse data in the reverse queue
                            reverse_queue.put((xreversedata.copy(), yreversedata.copy()))  # Use .copy() to keep the current state
        
                        elif 'clear' in item:
                            # Reset data
                            yrawforward.clear()
                            yrawreverse.clear()
                            xforwarddata.clear()
                            xreversedata.clear()
                            yforwarddata.clear()
                            yreversedata.clear()
        
                except socket.error as e:
                    print(f"Socket error: {e}")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    break
        
            clientsocket.close()
        
        def server_loop():
            """
            Main server loop to accept new client connections.
            """
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((socket.gethostname(), 1234))
            server_socket.listen(5)
            
            # Server is ready, set the event
            server_ready_event.set()
            print("Server is running and ready to accept connections.")
            
            while True:
                try:
                    client, address = server_socket.accept()
                    print(f"Accepted connection from {address}")
                    client_thread = threading.Thread(target=handle_client, args=(client,))
                    client_thread.daemon = True
                    client_thread.start()
                except socket.error as e:
                    print(f"Server socket error: {e}")
                    break
                except Exception as e:
                    print(f"Error in server loop: {e}")
                    break
            server_socket.close()
        
        # Start the server in a separate thread
        server_thread = threading.Thread(target=server_loop, daemon=True)
        server_thread.start()
    
    def stop_server():
        """
        Stops the server and closes any open client connections.
        """
        global clientsocket
        if clientsocket:
            clientsocket.close()
            clientsocket = None
    
    def run_rotarycaltest():
        """
        Runs the rotary calibration test. Handles setup, execution, and resource cleanup.
        """
        # Save user inputs before closing
        user_data = {
            "axis_name": rot_axis.get(),
            "start_position": rot_start.get(),
            "travel": rot_travel.get(),
            "step_size": rot_step.get(),
            "units": rot_units.get(),
            "stent": rot_diam.get(),
            "controller": rot_cont.get(),
            "system_serial_number": rot_sys.get(),
            "stage_serial_number": rot_st.get(),
            "operator": rot_opName.get(),
            "part_number": rot_st_type.get(),
            "temp": rot_temp.get(),
            "comments": rot_comm.get(),
            "col_axis": rot_col.get()
        }
        save_user_inputs(user_data)
        
        try:
            rotarycaltest()
        finally:
            gc.collect()
            window.after(0, btn_run_rot.config, {'state': tk.NORMAL})
            cleanup_resources()
            

    def rotarycaltest():
        axis = str(rot_axis.get())
        num_readings = 5
        dwell = 1
        step_size = float(rot_step.get())
        travel = float(rot_travel.get())
        temp = float(rot_temp.get())
        start_pos = float(rot_start.get())
        if units != 'deg':
            dia = float(rot_diam.get())
        else:
            dia = rot_diam.get()
        sys_serial = str(rot_sys.get())
        st_serial = str(rot_st.get())
        comments = str(rot_comm.get())
        stage_type = str(rot_st_type.get())
        oper = str(rot_opName.get())
        col_axis = str(rot_col.get())
        
        global rot_cal, controller
        
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
                else:
                    messagebox.showerror('Update Software', 'Update Hyperwire firmware and try again')
            connected_axes = {}
            non_virtual_axes = []

            number_of_axes = controller.runtime.parameters.axes.count

            if number_of_axes <= 12:
                for axis_index in range(0,11):

                    #try:            
                    # Create status item configuration object
                    status_item_configuration = a1.StatusItemConfiguration()
                                
                    # Add this axis status word to object
                    status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
                    
                    # Get axis status word from controller
                    result = controller.runtime.status.get_status_items(status_item_configuration)
                    axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
                    
                    # Check NotVirtual bit of axis status word
                    if (axis_status & 1 << 13) > 0:
                        connected_axes[controller.runtime.parameters.axes[axis_index].identification.axisname.value] = axis_index
                    #except:
                        #print('2')
                        #for key in connected_axes.items():
                            #if key == axis:
                                #print(key)
                                #break
                        #else:
                            #print('3')
                            #axis_no += 1
                            #pass

                for key,value in connected_axes.items():
                    non_virtual_axes.append(key)
                    
                if len(non_virtual_axes) == 0:
                    try:
                        controller = a1.Controller.connect_usb()
                    except:
                        messagebox.showerror('No Device', 'No Devices Present. Check Connections.')    
            else:
                for axis_index in range(0,32):
                
                    #try:            
                    # Create status item configuration object
                    status_item_configuration = a1.StatusItemConfiguration()
                                
                    # Add this axis status word to object
                    status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
                    
                    # Get axis status word from controller
                    result = controller.runtime.status.get_status_items(status_item_configuration)
                    axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
                    
                    # Check NotVirtual bit of axis status word
                    if (axis_status & 1 << 13) > 0:
                        connected_axes[controller.runtime.parameters.axes[axis_index].identification.axisname.value] = axis_index
                    #except:
                        #print('2')
                        #for key in connected_axes.items():
                            #if key == axis:
                                #print(key)
                                #break
                        #else:
                            #print('3')
                            #axis_no += 1
                            #pass
                
                for key,value in connected_axes.items():
                    non_virtual_axes.append(key)
                    
                if len(non_virtual_axes) == 0:
                    try:
                        controller = a1.Controller.connect_usb()
                    except:
                        messagebox.showerror('No Device', 'No Devices Present. Check Connections.')

            rot_cal = rotary_cal(
                axis, num_readings, dwell, step_size, travel, units, dia, test_type, sys_serial, 
                st_serial, comments, temp, start_pos, drive, stage_type, oper, txt_outStr, window
            )
            rot_cal.a1_test(controller)
        else:
            rot_cal = rotary_cal(
                axis, num_readings, dwell, step_size, travel, units, dia, test_type, sys_serial, 
                st_serial, comments, temp, start_pos, drive, stage_type, oper, txt_outStr, window, 
                is_cal=is_cal, col_axis=col_axis
            )
            rot_cal.test()
    
    def cleanup_resources():
        """
        Cleans up resources such as threads, connections, and resets global states.
        """
        global plot_thread, is_plot_running
        is_plot_running = False
        plot_thread = None
        if clientsocket:
            clientsocket.close()
        gc.collect()    
    
    def import_data_rotary():
        global rot_cal

        axis = str(rot_axis.get())
        num_readings = 5
        dwell = 1
        step_size = float(rot_step.get())
        travel = float(rot_travel.get())
        temp = float(rot_temp.get())
        start_pos = float(rot_start.get())
        if units != 'deg':
            dia = float(rot_diam.get())
        else:
            dia = rot_diam.get()
        sys_serial = str(rot_sys.get())
        st_serial = str(rot_st.get())
        comments = str(rot_comm.get())
        stage_type = str(rot_st_type.get())
        oper = str(rot_opName.get())

        rot_cal = rotary_cal(
            axis,
            num_readings,
            dwell,
            step_size,
            travel,
            units,
            dia,
            test_type,
            sys_serial,
            st_serial,
            comments,
            temp,
            start_pos,
            drive,
            stage_type,
            oper,
            txt_outStr,
            window
        )

        rot_cal.import_data()
        
    def test_type_def():
        global test_type
        if rot_direction.get() == "uni":
            test_type = 'Unidirectional'
        elif rot_direction.get() == "bi":
            test_type = 'Bidirectional'
        else:
            test_type = 'None'

    def unit_def():
        global units
        if rot_units.get() == 'deg':
            rot_diam.set('None')
            units = 'deg'
            ent_stent["state"] = tk.DISABLED
        elif rot_units.get() == 'mm':
            units = 'mm'
            ent_stent["state"] = tk.NORMAL
        elif rot_units.get() == 'in':
            units = 'in'
            ent_stent["state"] = tk.NORMAL
        else:
            units = 'None'
            ent_stent["state"] = tk.DISABLED

    def drive_def():
        global drive
        global is_cal
        if rot_cont.get() == 'a1':
            cbx_cal["state"] = tk.DISABLED
            ent_col['state'] = tk.DISABLED
            rot_cal.set(0)
            is_cal = 0
            drive = 'Automation1'
        elif rot_cont.get() == 'other':
            cbx_cal["state"] = tk.NORMAL
            ent_col['state'] = tk.NORMAL
            drive = 'Other'
            if rot_cal.get() == 1:
                is_cal = 1
            else:
                is_cal = 0
        else:
            drive = 'None'

    def cal_def():
        global is_cal
        if rot_cal.get() == 1:
            is_cal = 1
        else:
            is_cal = 0

    def open_rotary_Plot():
        sys.stdout = TextLogger(txt_outStr)

        axis = rot_axis.get()
        sys_serial = rot_sys.get()

        start_path = ('O:/')
        folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(start_path) for dir_name in dirs if str(sys_serial[0:6]) in dir_name), None)
        pdf_file_path = folder_path + '/Customer Files/Plots'
        print(pdf_file_path)

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
    
    # Rotary Calibration Tab UI Elements

    # Test Type Selection
    lbl_test = tk.Label(master=tab1, text="Select Test Type:")
    lbl_test.grid(row=test_row, column=0, padx=5, pady=5)
    
    rot_direction = tk.StringVar(value=0)
    uni_dir = tk.Radiobutton(master=tab1, text="Unidirectional", variable=rot_direction, value="uni", command=test_type_def)
    uni_dir.grid(row=test_row, column=1, padx=5, pady=5)
    
    bi_dir = tk.Radiobutton(master=tab1, text="Bidirectional", variable=rot_direction, value="bi", command=test_type_def)
    bi_dir.grid(row=test_row, column=2, padx=5, pady=5)
    
    # Axis Name Input
    lbl_axis = tk.Label(master=tab1, text="Axis Name", width=25, height=1)
    lbl_axis.grid(row=axName_row, column=0, padx=5, pady=5)
    
    rot_axis = tk.StringVar(value=rot_axis_value)
    ent_axis = tk.Entry(master=tab1, textvariable=rot_axis, width=25)
    ent_axis.grid(row=axName_row, column=1, padx=5, pady=5)
    
    # Starting Position Input
    lbl_st = tk.Label(master=tab1, text="Starting Position (deg)", width=25, height=1)
    lbl_st.grid(row=ll_row, column=0, padx=5, pady=5)
    
    rot_start = tk.DoubleVar(value=rot_start_value)
    ent_start_pos = tk.Entry(master=tab1, textvariable=rot_start, width=25)
    ent_start_pos.grid(row=ll_row, column=1, padx=5, pady=5)
    
    # Total Travel Input
    lbl_travel = tk.Label(master=tab1, text="Total Travel (deg)", width=25, height=1)
    lbl_travel.grid(row=ul_row, column=0, padx=5, pady=5)
    
    rot_travel = tk.DoubleVar(value=rot_travel_value)
    ent_travel = tk.Entry(master=tab1, textvariable=rot_travel, width=25)
    ent_travel.grid(row=ul_row, column=1, padx=5, pady=5)
    
    # Step Size Input
    lbl_step_size = tk.Label(master=tab1, text="Step Size (deg)", width=25, height=1)
    lbl_step_size.grid(row=ts_row, column=0, padx=5, pady=5)
    
    rot_step = tk.DoubleVar(value=rot_step_value)
    ent_step_size = tk.Entry(master=tab1, textvariable=rot_step, width=25)
    ent_step_size.grid(row=ts_row, column=1, padx=5, pady=5)
    
    # Units Selection
    lbl_units = tk.Label(master=tab1, text="Units:")
    lbl_units.grid(row=filt_row, column=0, padx=5, pady=5)
    
    rot_units = tk.StringVar(value=0)
    cbx_deg = tk.Radiobutton(master=tab1, text="Degrees", variable=rot_units, value='deg', command=unit_def)
    cbx_deg.grid(row=filt_row, column=1, padx=5, pady=5)
    
    cbx_mm = tk.Radiobutton(master=tab1, text="Millimeters", variable=rot_units, value='mm', command=unit_def)
    cbx_mm.grid(row=filt_row, column=2, padx=5, pady=5)
    
    cbx_in = tk.Radiobutton(master=tab1, text="Inches", variable=rot_units, value='in', command=unit_def)
    cbx_in.grid(row=filt_row, column=3, padx=5, pady=5)
    
    # Stent Diameter Input (Disabled)
    lbl_stent = tk.Label(master=tab1, text="Stent Diameter (mm)", width=25, height=1)
    lbl_stent.grid(row=eq_row, column=0, padx=5, pady=5)
    
    rot_diam = tk.StringVar(value=rot_stent_value)
    ent_stent = tk.Entry(master=tab1, textvariable=rot_diam, width=25, state=tk.DISABLED)
    ent_stent.grid(row=eq_row, column=1, padx=5, pady=5)
    
    # Controller Selection
    lbl_drive = tk.Label(master=tab1, text="Controller:")
    lbl_drive.grid(row=eqa_row, column=0, padx=5, pady=5)
    
    rot_cont = tk.StringVar(value=0)
    cbx_a1 = tk.Radiobutton(master=tab1, text="Automation1", variable=rot_cont, value='a1', command=drive_def)
    cbx_a1.grid(row=eqa_row, column=1, padx=5, pady=5)
    
    cbx_other = tk.Radiobutton(master=tab1, text="Other", variable=rot_cont, value='other', command=drive_def)
    cbx_other.grid(row=eqa_row, column=2, padx=5, pady=5)
    
    # Calibration Checkbox (Disabled)
    rot_cal = tk.IntVar(value=0)
    cbx_cal = tk.Checkbutton(master=tab1, text="Calibrated?", variable=rot_cal, onvalue=1, offvalue=0, state=tk.DISABLED, command=cal_def)
    cbx_cal.grid(row=eqa_row, column=3, padx=5, pady=5)
    
    # System Serial Number Input
    lbl_serial = tk.Label(master=tab1, text="System Serial Number", width=25, height=1)
    lbl_serial.grid(row=sn_row, column=0, padx=5, pady=5)
    
    rot_sys = tk.StringVar(value=rot_sys_value)
    ent_serial = tk.Entry(master=tab1, textvariable=rot_sys, width=25)
    ent_serial.grid(row=sn_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Stage Serial Number Input
    lbl_st_serial = tk.Label(master=tab1, text="Stage Serial Number", width=25, height=1)
    lbl_st_serial.grid(row=stage_row, column=0, padx=5, pady=5)
    
    rot_st = tk.StringVar(value=rot_st_value)
    ent_st_serial = tk.Entry(master=tab1, textvariable=rot_st, width=25)
    ent_st_serial.grid(row=stage_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Operator Input
    lbl_op = tk.Label(master=tab1, text="Operator", width=25, height=1)
    lbl_op.grid(row=op_row, column=0, padx=5, pady=5)
    
    rot_opName = tk.StringVar(value=rot_op_value)
    ent_op = tk.Entry(master=tab1, textvariable=rot_opName, width=25)
    ent_op.grid(row=op_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Stage Part Number Input
    lbl_stage = tk.Label(master=tab1, text="Stage Part Number", width=25, height=1)
    lbl_stage.grid(row=cv_row, column=0, padx=5, pady=5)
    
    rot_st_type = tk.StringVar(value=rot_part_value)
    ent_stage = tk.Entry(master=tab1, textvariable=rot_st_type, width=25)
    ent_stage.grid(row=cv_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Temperature Input
    lbl_temp = tk.Label(master=tab1, text="Temp", width=25, height=1)
    lbl_temp.grid(row=ol_row, column=0, padx=5, pady=5)
    
    rot_temp = tk.DoubleVar(value=rot_temp_value)
    ent_temp = tk.Entry(master=tab1, textvariable=rot_temp, width=25)
    ent_temp.grid(row=ol_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Comments Input
    lbl_comments = tk.Label(master=tab1, text="Comments", width=25, height=1)
    lbl_comments.grid(row=pm_row, column=0, padx=5, pady=5)
    
    rot_comm = tk.StringVar(value=rot_comm_value)
    ent_comments = tk.Entry(master=tab1, textvariable=rot_comm, width=25)
    ent_comments.grid(row=pm_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Collimator Axis Input (Disabled)
    lbl_col = tk.Label(master=tab1, text="Collimator Axis", width=25, height=1)
    lbl_col.grid(row=col_row, column=0, padx=5, pady=5)
    
    rot_col = tk.StringVar(value=rot_col_value)
    ent_col = tk.Entry(master=tab1, textvariable=rot_col, state=tk.DISABLED, width=25)
    ent_col.grid(row=col_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Import Data Button
    btn_import_rot = tk.Button(master=tab1, text="Import Data", width=30, height=1, command=import_data_rotary)
    btn_import_rot.grid(row=run_row, column=1, padx=5, pady=5)
    
    lbl_import_rot = tk.Label(master=tab1, text='', anchor='w')
    lbl_import_rot.grid(row=run_row, column=1, padx=5, pady=5, columnspan=3)
    
    # Run and Open Plot Buttons
    btn_run_rot = tk.Button(master=tab1, text="Run", width=25, height=1, command=start_rotarycaltest)
    btn_run_rot.grid(row=run_row, column=0, padx=5, pady=5)
    
    btn_open_rot = tk.Button(master=tab1, text="Open Plot", width=25, height=1, command=open_rotary_Plot)
    btn_open_rot.grid(row=run_row, column=2, padx=5, pady=5)


    # Create a Frame to hold the Text widget and the Scrollbar
    frame = tk.Frame(master=tab1)

    # Create the Text widget
    txt_outStr = tk.Text(master=frame, state=tk.DISABLED, height=10, fg='white', bg='black')

    # Create the Scrollbar widget
    outStr_scroll = tk.Scrollbar(master=frame, orient=tk.VERTICAL)

    # Link the Scrollbar to the Text widget
    txt_outStr.configure(yscrollcommand=outStr_scroll.set)
    outStr_scroll.config(command=txt_outStr.yview)

    # Pack the Text widget and the Scrollbar inside the Frame
    txt_outStr.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    outStr_scroll.pack(side=tk.LEFT, fill=tk.Y)

    # Grid the Frame containing the Text widget and the Scrollbar
    frame.grid(row=out_row, column=0, columnspan=7, padx=5, pady=5, sticky='nsew')

    # Create the logger object
    logger1 = TextLogger(txt_outStr)

    # Configure the grid to expand the Frame
    tab1.grid_rowconfigure(out_row, weight=1)
    tab1.grid_columnconfigure(0, weight=1)

    '''
    Tab 2: Angular Testing
    
    This tab is for running pitch, yaw, and roll tests
    '''
    
    def angular_live_plot():
        """
        Initialize and update the live plot for angular testing.
        """
        global ani1, ani2, col_axis_X, col_axis_Y
        fig1, ax1, canvas1 = setup_figure(tab2, 0, 4, col_axis_X, "Angular Errors", (17, 0))
        fig2, ax2, canvas2 = setup_figure(tab2, 11, 4, col_axis_Y, "", (7, 0))
    
        # Start server thread to handle incoming data
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
    
        # Create animations for the two plots
        ani1 = FuncAnimation(fig1, lambda frame: update_angular_plot(frame, ax1, ax2, canvas1, canvas2), interval=1000, cache_frame_data=False)
        ani2 = FuncAnimation(fig2, lambda frame: update_angular_plot(frame, ax1, ax2, canvas1, canvas2), interval=1000, cache_frame_data=False)
    
    def setup_figure(tab, row, column, ylabel, title, pady):
        """
        Set up a figure and axes for plotting.
        """
        plot_font = {'family': 'serif', 'weight': 'normal', 'size': 12}
        title_font = {'family': 'serif', 'weight': 'normal', 'size': 16}
        
        fig, ax = plt.subplots()
        ax.set_facecolor("white")
        ax.set_xlabel("Position", fontdict=plot_font, color='darkred')
        ax.set_ylabel(ylabel, fontdict=plot_font, color='darkred')
        if title:
            ax.set_title(title, fontdict=title_font)
        ax.grid(False)
    
        # Embed figure in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.get_tk_widget().grid(row=row, column=column, rowspan=10, columnspan=3, padx=1, pady=pady, sticky='nsew')
    
        return fig, ax, canvas
    
    def update_angular_plot(frame, ax1, ax2, canvas1, canvas2):
        """
        Update plots for angular data.
        """
        global xforwarddata, xreversedata, yforwarddata, yreversedata, zforwarddata, zreversedata
    
        # Clear axes for new data
        ax1.cla()
        ax2.cla()
    
        # Plot data on both axes
        plot_data(ax1, xforwarddata, yforwarddata, xreversedata, yreversedata, "Position", col_axis_X)
        plot_data(ax2, xforwarddata, zforwarddata, xreversedata, zreversedata, "Position", col_axis_Y)
    
        # Redraw canvases
        canvas1.draw()
        canvas2.draw()
    
    def plot_data(ax, xforward, yforward, xreverse, yreverse, xlabel, ylabel):
        """
        Plot forward and reverse data on a given axis.
        """
        ax.plot(xforward, yforward, color='b', marker='o')
        ax.plot(xreverse, yreverse, color='r', marker='x')
        ax.set_xlabel(xlabel, font={'family': 'serif', 'weight': 'normal', 'size': 12})
        ax.set_ylabel(ylabel, font={'family': 'serif', 'weight': 'normal', 'size': 12})
        ax.relim()
        ax.autoscale_view()
        ax.tick_params(axis='both', which='major', labelsize=10)
    
    def run_server():
        """
        Run a TCP server to receive data for plotting.
        """
        global clientsocket
        s = socket.socket(socket.AF)

    def angular_test_type_def():
        global test_type
        if ang_direction.get() == "uni":
            test_type = 'Unidirectional'
        elif ang_direction.get() == "bi":
            test_type = 'Bidirectional'
        else:
            test_type = 'None'
    
    def colaxis_def():
        global col_axis_X, col_axis_Y
        if ang_colaxisX.get() == 'pitch':
            col_axis_X = 'Pitch'
        elif ang_colaxisX.get() == 'yaw':
            col_axis_X = 'Yaw'
        elif ang_colaxisX.get() == 'roll':
            col_axis_X = 'Roll'
        if ang_colaxisY.get() == 'pitch':
            col_axis_Y = 'Pitch'
        elif ang_colaxisY.get() == 'yaw':
            col_axis_Y = 'Yaw'
        elif ang_colaxisY.get() == 'roll':
            col_axis_Y = 'Roll'

    def start_angulartest():
        global yrawforward,zrawforward,yrawreverse,zrawreverse,xforwarddata,xreversedata,yforwarddata,zforwarddata,zreversedata,yreversedata
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
        btn_run_ang.config(state=tk.DISABLED)
        threading.Thread(target=run_angulartest).start()

    def run_angulartest():
        global clientsocket
        # Save user inputs before closing
        user_data = {
            "axis_name": ang_axis.get(),
            "start_position": ang_start.get(),
            "travel": ang_travel.get(),
            "step_size": ang_step.get(),
            "controller": ang_cont.get(),
            "units": ang_units.get(),
            "system_serial_number": ang_sys.get(),
            "stage_serial_number": ang_st.get(),
            "operator": ang_opName.get(),
            "part_number": ang_st_type.get(),
            "temp": ang_temp.get(),
            "comments": ang_comm.get(),
        }
        save_user_inputs(user_data)
        try:
            angulartest()
        finally:
            gc.collect()                         
            clientsocket.close()
            window.after(0, btn_run_ang.config, {'state': tk.NORMAL})

    def angulartest():
        axis = str(ang_axis.get())
        start_pos = float(ang_start.get())
        travel = float(ang_travel.get())
        step_size = float(ang_step.get())
        drive = str(ang_cont.get())
        units = str(ang_units.get())
        num_readings = 5
        dwell = 1
        sys_serial = str(ang_sys.get())
        st_serial = str(ang_st.get())
        oper = str(ang_opName.get())
        stage_type = str(ang_st_type.get())
        temp = float(ang_temp.get())
        comments = str(ang_comm.get())

        global ang, controller
        
        threading.Thread(target=angular_live_plot).start()
        
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
                else:
                    messagebox.showerror('Update Software', 'Update Hyperwire firmware and try again')
            connected_axes = {}
            non_virtual_axes = []

            number_of_axes = controller.runtime.parameters.axes.count

            if number_of_axes <= 12:
                for axis_index in range(0,11):

                    #try:            
                    # Create status item configuration object
                    status_item_configuration = a1.StatusItemConfiguration()
                                
                    # Add this axis status word to object
                    status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
                    
                    # Get axis status word from controller
                    result = controller.runtime.status.get_status_items(status_item_configuration)
                    axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
                    
                    # Check NotVirtual bit of axis status word
                    if (axis_status & 1 << 13) > 0:
                        connected_axes[controller.runtime.parameters.axes[axis_index].identification.axisname.value] = axis_index
                    #except:
                        #print('2')
                        #for key in connected_axes.items():
                            #if key == axis:
                                #print(key)
                                #break
                        #else:
                            #print('3')
                            #axis_no += 1
                            #pass

                for key,value in connected_axes.items():
                    non_virtual_axes.append(key)
                    
                if len(non_virtual_axes) == 0:
                    try:
                        controller = a1.Controller.connect_usb()
                    except:
                        messagebox.showerror('No Device', 'No Devices Present. Check Connections.')    
            else:
                for axis_index in range(0,32):
                
                    #try:            
                    # Create status item configuration object
                    status_item_configuration = a1.StatusItemConfiguration()
                                
                    # Add this axis status word to object
                    status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
                    
                    # Get axis status word from controller
                    result = controller.runtime.status.get_status_items(status_item_configuration)
                    axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
                    
                    # Check NotVirtual bit of axis status word
                    if (axis_status & 1 << 13) > 0:
                        connected_axes[controller.runtime.parameters.axes[axis_index].identification.axisname.value] = axis_index
                    #except:
                        #print('2')
                        #for key in connected_axes.items():
                            #if key == axis:
                                #print(key)
                                #break
                        #else:
                            #print('3')
                            #axis_no += 1
                            #pass
                
                for key,value in connected_axes.items():
                    non_virtual_axes.append(key)
                    
                if len(non_virtual_axes) == 0:
                    try:
                        controller = a1.Controller.connect_usb()
                    except:
                        messagebox.showerror('No Device', 'No Devices Present. Check Connections.')

            ang = angular(
                test_type, axis, start_pos, travel, step_size, col_axis_X, col_axis_Y, drive, units, sys_serial, st_serial, oper, stage_type, temp, comments, num_readings, dwell, txt_outStr1, window
            )
            ang.a1_test(controller)
        else:
            ang = angular(
                test_type, axis, start_pos, travel, step_size, col_axis_X, col_axis_Y, drive, units, sys_serial, st_serial, oper, stage_type, temp, comments, num_readings, dwell, txt_outStr1, window
            )
            ang.test()
    
    def open_angular_Plot():
        sys.stdout = TextLogger(txt_outStr1)

        axis = ang_axis.get()
        sys_serial = ang_sys.get()

        start_path = ('O:/')
        folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(start_path) for dir_name in dirs if str(sys_serial[0:6]) in dir_name), None)
        pdf_file_path = folder_path + '/Customer Files/Plots'
        print(pdf_file_path)

        if os.path.exists(pdf_file_path):
            try:
                output_file = str(sys_serial + '-' + axis + f"_{col_axis_X}.pdf")
                pdf = pdf_file_path + '/' + output_file
                os.startfile(pdf)
            except:
                pass
            try:
                output_file = str(sys_serial + '-' + axis + f"_{col_axis_Y}.pdf")
                pdf = pdf_file_path + '/' + output_file
                os.startfile(pdf)
            except:
                pass
        else:
            print(f"File '{pdf_file_path}' does not exist.")
    
    def import_data_angular():
        global rot_cal

        axis = str(ang_axis.get())
        start_pos = float(ang_start.get())
        travel = float(ang_travel.get())
        step_size = float(ang_step.get())
        drive = str(ang_cont.get())
        units = str(ang_units.get())
        num_readings = 5
        dwell = 1
        sys_serial = str(ang_sys.get())
        st_serial = str(ang_st.get())
        oper = str(ang_opName.get())
        stage_type = str(ang_st_type.get())
        temp = float(ang_temp.get())
        comments = str(ang_comm.get())

        rot_cal = rotary_cal(
            axis,
            num_readings,
            dwell,
            step_size,
            travel,
            units,
            test_type,
            sys_serial,
            st_serial,
            comments,
            temp,
            start_pos,
            drive,
            stage_type,
            oper,
            txt_outStr,
            window
        )

        rot_cal.import_data()
    
    # Angular Testing Tab UI Elements

    # Test Type Selection
    lbl_test.grid(row=test_row, column=0, padx=5, pady=5)
    
    ang_direction = tk.StringVar(value=0)
    uni_dir = tk.Radiobutton(master=tab2, text="Unidirectional", variable=ang_direction, value="uni", command=angular_test_type_def)
    uni_dir.grid(row=test_row, column=1, padx=5, pady=5)
    
    bi_dir = tk.Radiobutton(master=tab2, text="Bidirectional", variable=ang_direction, value="bi", command=angular_test_type_def)
    bi_dir.grid(row=test_row, column=2, padx=5, pady=5)
    
    # Axis Name Input
    lbl_axis = tk.Label(master=tab2, text="Axis Name", width=25, height=1)
    lbl_axis.grid(row=axName_row, column=0, padx=5, pady=5)
    
    ang_axis = tk.StringVar(value=ang_axis_value)
    ent_axis = tk.Entry(master=tab2, textvariable=ang_axis, width=25)
    ent_axis.grid(row=axName_row, column=1, padx=5, pady=5)
    
    # Starting Position Input
    lbl_st = tk.Label(master=tab2, text="Starting Position", width=25, height=1)
    lbl_st.grid(row=ll_row, column=0, padx=5, pady=5)
    
    ang_start = tk.DoubleVar(value=ang_start_value)
    ent_start_pos = tk.Entry(master=tab2, textvariable=ang_start, width=25)
    ent_start_pos.grid(row=ll_row, column=1, padx=5, pady=5)
    
    # Total Travel Input
    lbl_travel = tk.Label(master=tab2, text="Total Travel", width=25, height=1)
    lbl_travel.grid(row=ul_row, column=0, padx=5, pady=5)
    
    ang_travel = tk.DoubleVar(value=ang_travel_value)
    ent_travel = tk.Entry(master=tab2, textvariable=ang_travel, width=25)
    ent_travel.grid(row=ul_row, column=1, padx=5, pady=5)
    
    # Step Size Input
    lbl_step_size = tk.Label(master=tab2, text="Step Size", width=25, height=1)
    lbl_step_size.grid(row=ts_row, column=0, padx=5, pady=5)
    
    ang_step = tk.DoubleVar(value=ang_step_value)
    ent_step_size = tk.Entry(master=tab2, textvariable=ang_step, width=25)
    ent_step_size.grid(row=ts_row, column=1, padx=5, pady=5)
    
    # Controller Selection Dropdown
    lbl_drive = tk.Label(master=tab2, text="Controller:", width=25, height=1)
    lbl_drive.grid(row=axName_row, column=2, padx=5, pady=5)
    
    drive_options = ['Automation1', 'A3200', 'Other']
    ang_cont = tk.StringVar(value=ang_controller_value)  # Set default value
    
    cont = tk.OptionMenu(tab2, ang_cont, *drive_options)
    cont.grid(row=ll_row, column=2, padx=5, pady=5)
    
    # Units Selection Dropdown
    lbl_units = tk.Label(master=tab2, text="Units:", width=25, height=1)
    lbl_units.grid(row=axName_row, column=3, padx=5, pady=5)
    
    unit_options = ['mm', 'um', 'in', 'm']
    ang_units = tk.StringVar(value=ang_units_value)  # Set default value
    
    un = tk.OptionMenu(tab2, ang_units, *unit_options)
    un.grid(row=ll_row, column=3, padx=5, pady=5)
    
    # Collimator X Selection
    lbl_xdir = tk.Label(master=tab2, text="Collimator X:")
    lbl_xdir.grid(row=eq_row, column=0, padx=5, pady=5)
    
    ang_colaxisX = tk.StringVar(value=0)
    cbx_xpitch = tk.Radiobutton(master=tab2, text="Pitch", variable=ang_colaxisX, value='pitch', command=colaxis_def)
    cbx_xpitch.grid(row=eq_row, column=1, padx=5, pady=5)
    
    cbx_xyaw = tk.Radiobutton(master=tab2, text="Yaw", variable=ang_colaxisX, value='yaw', command=colaxis_def)
    cbx_xyaw.grid(row=eq_row, column=2, padx=5, pady=5)
    
    cbx_xroll = tk.Radiobutton(master=tab2, text="Roll", variable=ang_colaxisX, value='roll', command=colaxis_def)
    cbx_xroll.grid(row=eq_row, column=3, padx=5, pady=5)
    
    # Collimator Y Selection
    lbl_ydir = tk.Label(master=tab2, text="Collimator Y:")
    lbl_ydir.grid(row=eqa_row, column=0, padx=5, pady=5)
    
    ang_colaxisY = tk.StringVar(value=0)
    cbx_ypitch = tk.Radiobutton(master=tab2, text="Pitch", variable=ang_colaxisY, value='pitch', command=colaxis_def)
    cbx_ypitch.grid(row=eqa_row, column=1, padx=5, pady=5)
    
    cbx_yyaw = tk.Radiobutton(master=tab2, text="Yaw", variable=ang_colaxisY, value='yaw', command=colaxis_def)
    cbx_yyaw.grid(row=eqa_row, column=2, padx=5, pady=5)
    
    cbx_yroll = tk.Radiobutton(master=tab2, text="Roll", variable=ang_colaxisY, value='roll', command=colaxis_def)
    cbx_yroll.grid(row=eqa_row, column=3, padx=5, pady=5)
    
    # System Serial Number Input
    lbl_serial = tk.Label(master=tab2, text="System Serial Number", width=25, height=1)
    lbl_serial.grid(row=sn_row, column=0, padx=5, pady=5)
    
    ang_sys = tk.StringVar(value=ang_sys_value)
    ent_serial = tk.Entry(master=tab2, textvariable=ang_sys, width=25)
    ent_serial.grid(row=sn_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Stage Serial Number Input
    lbl_st_serial = tk.Label(master=tab2, text="Stage Serial Number", width=25, height=1)
    lbl_st_serial.grid(row=stage_row, column=0, padx=5, pady=5)
    
    ang_st = tk.StringVar(value=ang_st_value)
    ent_st_serial = tk.Entry(master=tab2, textvariable=ang_st, width=25)
    ent_st_serial.grid(row=stage_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Operator Input
    lbl_op = tk.Label(master=tab2, text="Operator", width=25, height=1)
    lbl_op.grid(row=op_row, column=0, padx=5, pady=5)
    
    ang_opName = tk.StringVar(value=ang_op_value)
    ent_op = tk.Entry(master=tab2, textvariable=ang_opName, width=25)
    ent_op.grid(row=op_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Stage Part Number Input
    lbl_stage = tk.Label(master=tab2, text="Stage Part Number", width=25, height=1)
    lbl_stage.grid(row=cv_row, column=0, padx=5, pady=5)
    
    ang_st_type = tk.StringVar(value=ang_part_value)
    ent_stage = tk.Entry(master=tab2, textvariable=ang_st_type, width=25)
    ent_stage.grid(row=cv_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Temperature Input
    lbl_temp = tk.Label(master=tab2, text="Temp", width=25, height=1)
    lbl_temp.grid(row=ol_row, column=0, padx=5, pady=5)
    
    ang_temp = tk.DoubleVar(value=ang_temp_value)
    ent_temp = tk.Entry(master=tab2, textvariable=ang_temp, width=25)
    ent_temp.grid(row=ol_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Comments Input
    lbl_comments = tk.Label(master=tab2, text="Comments", width=25, height=1)
    lbl_comments.grid(row=pm_row, column=0, padx=5, pady=5)
    
    ang_comm = tk.StringVar(value=ang_comm_value)
    ent_comments = tk.Entry(master=tab2, textvariable=ang_comm, width=25)
    ent_comments.grid(row=pm_row, column=1, columnspan=3, padx=5, pady=5)
    
    # Import Data Button
    btn_import_ang = tk.Button(master=tab2, text="Import Data", width=30, height=1, command=import_data_angular)
    btn_import_ang.grid(row=run_row, column=1, padx=5, pady=5)
    
    lbl_import_ang = tk.Label(master=tab2, text='', anchor='w')
    lbl_import_ang.grid(row=run_row, column=1, padx=5, pady=5, columnspan=3)
    
    # Run and Open Plot Buttons
    btn_run_ang = tk.Button(master=tab2, text="Run", width=25, height=1, command=start_angulartest)
    btn_run_ang.grid(row=run_row, column=0, padx=5, pady=5)
    
    btn_open_ang = tk.Button(master=tab2, text="Open Plot", width=25, height=1, command=open_angular_Plot)
    btn_open_ang.grid(row=run_row, column=2, padx=5, pady=5)

    
    # Create a Frame to hold the Text widget and the Scrollbar
    frame1 = tk.Frame(tab2)

    # Create the Text widget
    txt_outStr1 = tk.Text(master=frame1, state=tk.DISABLED, height=10, fg='white', bg='black')

    # Create the Scrollbar widget
    outStr_scroll1 = tk.Scrollbar(master=frame1, orient=tk.VERTICAL)

    # Link the Scrollbar to the Text widget
    txt_outStr1.configure(yscrollcommand=outStr_scroll1.set)
    outStr_scroll1.config(command=txt_outStr1.yview)

    # Pack the Text widget and the Scrollbar inside the Frame
    txt_outStr1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    outStr_scroll1.pack(side=tk.LEFT, fill=tk.Y)

    # Grid the Frame containing the Text widget and the Scrollbar
    frame1.grid(row=out_row, column=0, columnspan=7, padx=5, pady=5, sticky='nsew')

    # Create the logger object
    logger1 = TextLogger(txt_outStr1)

    # Configure the grid to expand the Frame
    tab2.grid_rowconfigure(out_row, weight=1)
    tab2.grid_columnconfigure(0, weight=1)
    
    def on_closing():
        # Save user inputs before closing
        user_data = {
            "axis_name": ang_axis.get(),
            "start_position": ang_start.get(),
            "travel": ang_travel.get(),
            "step_size": ang_step.get(),
            "controller": ang_cont.get(),
            "units": ang_units.get(),
            "system_serial_number": ang_sys.get(),
            "stage_serial_number": ang_st.get(),
            "operator": ang_opName.get(),
            "part_number": ang_st_type.get(),
            "temp": ang_temp.get(),
            "comments": ang_comm.get(),
        }
        
        user_data = {
            "axis_name": rot_axis.get(),
            "start_position": rot_start.get(),
            "travel": rot_travel.get(),
            "step_size": rot_step.get(),
            "units": rot_units.get(),
            "stent": rot_diam.get(),
            "controller": rot_cont.get(),
            "system_serial_number": rot_sys.get(),
            "stage_serial_number": rot_st.get(),
            "operator": rot_opName.get(),
            "part_number": rot_st_type.get(),
            "temp": rot_temp.get(),
            "comments": rot_comm.get(),
            "col_axis": rot_col.get()
        }
        
        save_user_inputs(user_data)
        window.destroy()
    
    window.protocol("WM_DELETE_WINDOW", on_closing)
    
    window.mainloop()

if __name__ == '__main__':
    UI()
    
