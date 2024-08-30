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
    rot_units_value = stored_data.get("units", '')
    rot_stent_value = stored_data.get("stent", '')
    rot_cont_value = stored_data.get("controller", '')
    rot_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    rot_st_value = stored_data.get("stage_serial_number", '"Stage Serial Number"')
    rot_op_value = stored_data.get("operator", '"Your Initials"')
    rot_part_value = stored_data.get("part_number", '"Part Number"')
    rot_temp_value = stored_data.get("temp", 20)
    rot_comm_value = stored_data.get("comments", "")
    rot_col_value = stored_data.get("col_axis", '')
    
    def rotary_live_plot():
        global xforwarddata,xreversedata,yforwarddata,yreversedata
        global fig,ax, plot_mean
        
        plot_font = {'family': 'serif', 'weight': 'normal', 'size': 14}
        title_font = {'family': 'serif', 'weight': 'normal', 'size': 16}
        
        # Create a Figure and Axes for the plot
        fig, ax = plt.subplots()
        ax.set_facecolor("white")
        ax.set_xlabel("Position", fontdict=plot_font, color='darkred')
        ax.set_ylabel("Accuracy", fontdict=plot_font, color='darkred')
        ax.set_title("Live Plot of Position vs Accuracy", fontdict=title_font)
        
        canvas = FigureCanvasTkAgg(fig, master=tab1,)
        canvas.get_tk_widget().grid(row=0, column=4, rowspan=21, columnspan=3, padx=1, pady=(13,0), sticky='nsew')
        
        ax.grid(False)
        
        '''
        Using Queue Method
        
        
        global queue
        queue = Queue(maxsize=0)
        
        def update_plot(frame):
            if not queue.empty():
                xdata, ydata = queue.get()
    
                ax.cla()  # Clear the current plot
                ax.plot(xdata, ydata)  # Plot all the data points
                print(xdata,ydata)
                
        
        global ani
        ani = FuncAnimation(fig, update_plot, interval=100)
        '''
        def update_plot(frame):
            global xforwarddata,xreversedata,yforwarddata,yreversedata

            ax.cla()  # Clear the current plot

            ax.plot(xforwarddata, yforwarddata, color='b', marker='o')
            ax.plot(xreversedata, yreversedata, color='r', marker='x')# Plot all the data points
            ax.relim()
            ax.autoscale_view()
            
            ax.set_xlabel("Position", font=plot_font)
            ax.set_ylabel("Accuracy", font=plot_font)
            ax.set_title("Live Accuracy Plot", fontsize=16)
            
            # Set the font size for the tick labels
            ax.tick_params(axis='both', which='major', labelsize=12)
            
            canvas.draw()
            
        def handle_client(clientsocket):
            global yrawforward,yrawreverse,xforwarddata,xreversedata,yforwarddata,yreversedata,plot_mean
            while True:
                data = clientsocket.recv(1024)
                if not data:
                    break
                data = data.decode('utf-8').split(',')
                forward_data = None
                reverse_data = None
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
                        #yforwarddata.append(y)
                        yforwarddata = [i - plot_mean for i in yrawforward]
                        break
                    if 'clear' in item:
                        yrawforward = []
                        yrawreverse = []
                        xforwarddata = []
                        xreversedata = []
                        yforwarddata = []
                        yreversedata = []
                    
                    if "reverse_fbk" in item:
                        reverse_fbk = item.split(":")[1].strip()
                        x = float(reverse_fbk)
                        xreversedata.append(x)
                    elif "reverse_col" in item:
                        reverse_data = item.split(":")[1].strip()
                        y = float(reverse_data)
                        yrawreverse.append(y)
                        #yreversedata.append(y)
                        yreversedata = [i - plot_mean for i in yrawreverse]
                        break
            gc.collect()                         
            clientsocket.close()

        def run_server():
            global clientsocket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((socket.gethostname(), 1234))
            s.listen(5)
        
            while True:
                # now our endpoint knows about the OTHER endpoint.
                clientsocket, address = s.accept()
                threading.Thread(target=handle_client, args=(clientsocket,)).start()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        global ani
        ani = FuncAnimation(fig, update_plot, interval=100,cache_frame_data=False)        
        
    def ask_user_input(prompt, logger):
        logger.write(prompt + "\n")
        return logger.read_input()

    def start_rotarycaltest():
        global yrawforward,yrawreverse,xforwarddata,xreversedata,yforwarddata,yreversedata
        yrawforward = []
        yrawreverse = []
        xforwarddata = []
        xreversedata = []
        yforwarddata = []
        yreversedata = []
        btn_run_rot.config(state=tk.DISABLED)
        threading.Thread(target=run_rotarycaltest).start()
        threading.Thread(target=rotary_live_plot).start()

    def run_rotarycaltest():
        global clientsocket
        # Save user inputs before closing
        user_data = {
            "axis_name": ax1.get(),
            "start_position": start1.get(),
            "travel": trav1.get(),
            "step_size": step1.get(),
            "units": unit1.get(),
            "stent": diam1.get(),
            "controller": cont1.get(),
            "system_serial_number": sys1.get(),
            "stage_serial_number": st1.get(),
            "operator": opName1.get(),
            "part_number": st_type1.get(),
            "temp": tem1.get(),
            "comments": comm1.get(),
            "col_axis": col1.get()
        }
        save_user_inputs(user_data)
        try:
            rotarycaltest()
        finally:
            #ani.event_source.stop()
            gc.collect()  
            clientsocket.close()
            window.after(0, btn_run_rot.config, {'state': tk.NORMAL})
            

    def rotarycaltest():
        axis = str(ax1.get())
        num_readings = 5
        dwell = 1
        step_size = float(step1.get())
        travel = float(trav1.get())
        temp = float(tem1.get())
        start_pos = float(start1.get())
        if units != 'deg':
            dia = float(diam1.get())
        else:
            dia = diam1.get()
        sys_serial = str(sys1.get())
        st_serial = str(st1.get())
        comments = str(comm1.get())
        stage_type = str(st_type1.get())
        oper = str(opName1.get())
        col_axis = str(col1.get())
        
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

    def import_data_rotary():
        global rot_cal

        axis = ax1.get()
        num_readings = 5
        dwell = 1
        step_size = float(step1.get())
        travel = float(trav1.get())
        temp = float(tem1.get())
        start_pos = float(start1.get())
        dia = diam1.get()
        sys_serial = sys1.get()
        st_serial = st1.get()
        comments = comm1.get()
        stage_type = st_type1.get()
        oper = opName1.get()

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
        if direction1.get() == "uni":
            test_type = 'Unidirectional'
        elif direction1.get() == "bi":
            test_type = 'Bidirectional'
        else:
            test_type = 'None'

    def unit_def():
        global units
        if unit1.get() == 'deg':
            diam1.set('None')
            units = 'deg'
            ent_stent["state"] = tk.DISABLED
        elif unit1.get() == 'mm':
            units = 'mm'
            ent_stent["state"] = tk.NORMAL
        elif unit1.get() == 'in':
            units = 'in'
            ent_stent["state"] = tk.NORMAL
        else:
            units = 'None'
            ent_stent["state"] = tk.DISABLED

    def drive_def():
        global drive
        global is_cal
        if cont1.get() == 'a1':
            cbx_cal["state"] = tk.DISABLED
            ent_col['state'] = tk.DISABLED
            cal1.set(0)
            is_cal = 0
            drive = 'Automation1'
        elif cont1.get() == 'other':
            cbx_cal["state"] = tk.NORMAL
            ent_col['state'] = tk.NORMAL
            drive = 'Other'
            if cal1.get() == 1:
                is_cal = 1
            else:
                is_cal = 0
        else:
            drive = 'None'

    def cal_def():
        global is_cal
        if cal1.get() == 1:
            is_cal = 1
        else:
            is_cal = 0

    def open_rotary_Plot():
        sys.stdout = TextLogger(txt_outStr)

        axis = ax1.get()
        sys_serial = sys1.get()

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
    
    # Load stored data or set defaults
    rot_axis_value = stored_data.get("axis_name", "X")
    rot_start_value = stored_data.get("start_position", 0)
    rot_travel_value = stored_data.get("travel", 360)
    rot_step_value = stored_data.get("step_size", 15)
    rot_units_value = stored_data.get("units", '')
    rot_stent_value = stored_data.get("stent", '')
    rot_cont_value = stored_data.get("controller", '')
    rot_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    rot_st_value = stored_data.get("stage_serial_number", '"Stage Serial Number"')
    rot_op_value = stored_data.get("operator", '"Your Initials"')
    rot_part_value = stored_data.get("part_number", '"Part Number"')
    rot_temp_value = stored_data.get("temp", 20)
    rot_comm_value = stored_data.get("comments", "")
    rot_col_value = stored_data.get("col_axis", '')
    
    lbl_test = tk.Label(
        master=tab1,
        text="Select Test Type:",
    )

    lbl_test.grid(row=test_row, column=0, padx=5, pady=5)

    direction1 = tk.StringVar(value=0)

    uni_dir = tk.Radiobutton(
        master=tab1,
        text="Unidirectional",
        variable=direction1,
        value="uni",
        command=test_type_def
    )
    uni_dir.grid(row=test_row, column=1, padx=5, pady=5)

    bi_dir = tk.Radiobutton(
        master=tab1,
        text="Bidirectional",
        variable=direction1,
        value="bi",
        command=test_type_def
    )
    bi_dir.grid(row=test_row, column=2, padx=5, pady=5)

    lbl_axis = tk.Label(
        master=tab1,
        text="Axis Name",
        width=25,
        height=1,
    )
    lbl_axis.grid(row=axName_row, column=0, padx=5, pady=5)

    ax1 = tk.StringVar(value=rot_axis_value)
    ent_axis = tk.Entry(
        master=tab1,
        textvariable=ax1,
        width=25,
    )
    ent_axis.grid(row=axName_row, column=1, padx=5, pady=5)

    lbl_st = tk.Label(
        master=tab1,
        text="Starting Position (deg)",
        width=25,
        height=1,
    )
    lbl_st.grid(row=ll_row, column=0, padx=5, pady=5)

    start1 = tk.DoubleVar(value=rot_start_value)
    ent_start_pos = tk.Entry(
        master=tab1,
        textvariable=start1,
        width=25,
    )
    ent_start_pos.grid(row=ll_row, column=1, padx=5, pady=5)

    lbl_travel = tk.Label(
        master=tab1,
        text="Total Travel (deg)",
        width=25,
        height=1,
    )
    lbl_travel.grid(row=ul_row, column=0, padx=5, pady=5)

    trav1 = tk.DoubleVar(value=rot_travel_value)
    ent_travel = tk.Entry(
        master=tab1,
        textvariable=trav1,
        width=25,
    )
    ent_travel.grid(row=ul_row, column=1, padx=5, pady=5)

    lbl_step_size = tk.Label(
        master=tab1,
        text="Step Size (deg)",
        width=25,
        height=1,
    )
    lbl_step_size.grid(row=ts_row, column=0, padx=5, pady=5)

    step1 = tk.DoubleVar(value=rot_step_value)
    ent_step_size = tk.Entry(
        master=tab1,
        textvariable=step1,
        width=25,
    )
    ent_step_size.grid(row=ts_row, column=1, padx=5, pady=5)

    lbl_units = tk.Label(
        master=tab1,
        text="Units:",
    )
    lbl_units.grid(row=filt_row, column=0, padx=5, pady=5)

    unit1 = tk.StringVar(value=rot_units_value)
    cbx_deg = tk.Radiobutton(
        master=tab1,
        text="Degrees",
        variable=unit1,
        value='deg',
        command=unit_def
    )
    cbx_deg.grid(row=filt_row, column=1, padx=5, pady=5)

    cbx_mm = tk.Radiobutton(
        master=tab1,
        text="Millimeters",
        variable=unit1,
        value='mm',
        command=unit_def
    )
    cbx_mm.grid(row=filt_row, column=2, padx=5, pady=5)

    cbx_in = tk.Radiobutton(
        master=tab1,
        text="Inches",
        variable=unit1,
        value='in',
        command=unit_def
    )
    cbx_in.grid(row=filt_row, column=3, padx=5, pady=5)

    lbl_stent = tk.Label(
        master=tab1,
        text="Stent Diameter (mm)",
        width=25,
        height=1,
    )
    lbl_stent.grid(row=eq_row, column=0, padx=5, pady=5)

    diam1 = tk.StringVar(value=rot_stent_value)
    ent_stent = tk.Entry(
        master=tab1,
        textvariable=diam1,
        width=25,
        state=tk.DISABLED
    )
    ent_stent.grid(row=eq_row, column=1, padx=5, pady=5)

    lbl_drive = tk.Label(
        master=tab1,
        text="Controller:",
    )
    lbl_drive.grid(row=eqa_row, column=0, padx=5, pady=5)

    cont1 = tk.StringVar(value=rot_cont_value)

    cbx_a1 = tk.Radiobutton(
        master=tab1,
        text="Automation1",
        variable=cont1,
        value='a1',
        command=drive_def
    )
    cbx_a1.grid(row=eqa_row, column=1, padx=5, pady=5)

    cbx_other = tk.Radiobutton(
        master=tab1,
        text="Other",
        variable=cont1,
        value='other',
        command=drive_def
    )
    cbx_other.grid(row=eqa_row, column=2, padx=5, pady=5)

    cal1 = tk.IntVar(value=0)
    cbx_cal = tk.Checkbutton(
        master=tab1,
        text="Calibrated?",
        variable=cal1,
        onvalue=1,
        offvalue=0,
        state=tk.DISABLED,
        command=cal_def
    )
    cbx_cal.grid(row=eqa_row, column=3, padx=5, pady=5)

    lbl_serial = tk.Label(
        master=tab1,
        text="System Serial Number",
        width=25,
        height=1,
    )
    lbl_serial.grid(row=sn_row, column=0, padx=5, pady=5)

    sys1 = tk.StringVar(value=rot_sys_value)
    ent_serial = tk.Entry(
        master=tab1,
        textvariable=sys1,
        width=25,
    )
    ent_serial.grid(row=sn_row, column=1, columnspan=3, padx=5, pady=5)

    lbl_st_serial = tk.Label(
        master=tab1,
        text="Stage Serial Number",
        width=25,
        height=1,
    )
    lbl_st_serial.grid(row=stage_row, column=0, padx=5, pady=5)

    st1 = tk.StringVar(value=rot_st_value)
    ent_st_serial = tk.Entry(
        master=tab1,
        textvariable=st1,
        width=25,
    )
    ent_st_serial.grid(row=stage_row, column=1, columnspan=3, padx=5, pady=5)

    lbl_op = tk.Label(
        master=tab1,
        text="Operator",
        width=25,
        height=1,
    )
    lbl_op.grid(row=op_row, column=0, padx=5, pady=5)

    opName1 = tk.StringVar(value=rot_op_value)
    ent_op = tk.Entry(
        master=tab1,
        textvariable=opName1,
        width=25,
    )
    ent_op.grid(row=op_row, column=1, columnspan=3, padx=5, pady=5)

    lbl_stage = tk.Label(
        master=tab1,
        text="Stage Part Number",
        width=25,
        height=1,
    )
    lbl_stage.grid(row=cv_row, column=0, padx=5, pady=5)

    st_type1 = tk.StringVar(value=rot_part_value)
    ent_stage = tk.Entry(
        master=tab1,
        textvariable=st_type1,
        width=25,
    )
    ent_stage.grid(row=cv_row, column=1, columnspan=3, padx=5, pady=5)

    lbl_temp = tk.Label(
        master=tab1,
        text="Temp",
        width=25,
        height=1,
    )
    lbl_temp.grid(row=ol_row, column=0, padx=5, pady=5)

    tem1 = tk.DoubleVar(value=rot_temp_value)
    ent_temp = tk.Entry(
        master=tab1,
        textvariable=tem1,
        width=25,
    )
    ent_temp.grid(row=ol_row, column=1, columnspan=3, padx=5, pady=5)

    lbl_comments = tk.Label(
        master=tab1,
        text="Comments",
        width=25,
        height=1,
    )
    lbl_comments.grid(row=pm_row, column=0, padx=5, pady=5)

    comm1 = tk.StringVar(value=rot_comm_value)
    ent_comments = tk.Entry(
        master=tab1,
        textvariable=comm1,
        width=25,
    )
    ent_comments.grid(row=pm_row, column=1, columnspan=3, padx=5, pady=5)

    lbl_col = tk.Label(
        master=tab1,
        text="Collimator Axis",
        width=25,
        height=1,
    )
    lbl_col.grid(row=col_row, column=0, padx=5, pady=5)

    col1 = tk.StringVar(value=rot_col_value)
    ent_col = tk.Entry(
        master=tab1,
        textvariable=col1,
        state=tk.DISABLED,
        width=25,
    )
    ent_col.grid(row=col_row, column=1, columnspan=3, padx=5, pady=5)

    btn_import_rot = tk.Button(
        master=tab1,
        text="Import Data",
        width=30,
        height=1,
        command=import_data_rotary
    )
    btn_import_rot.grid(row=run_row, column=1, padx=5, pady=5)

    lbl_import_rot = tk.Label(
        master=tab1,
        text='',
        anchor='w',
    )

    lbl_import_rot.grid(row=run_row, column=1, padx=5, pady=5, columnspan=3)

    btn_run_rot = tk.Button(
        master=tab1,
        text="Run",
        width=25,
        height=1,
        command=start_rotarycaltest
    )

    btn_run_rot.grid(row=run_row, column=0, padx=5, pady=5)

    btn_open_rot = tk.Button(
        master=tab1,
        text="Open Plot",
        width=25,
        height=1,
        command=open_rotary_Plot
    )

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
    
    def rot_on_closing():
        # Save user inputs before closing
        user_data = {
            "axis_name": ax1.get(),
            "start_position": start1.get(),
            "travel": trav1.get(),
            "step_size": step1.get(),
            "units": unit1.get(),
            "stent": diam1.get(),
            "controller": cont1.get(),
            "system_serial_number": sys1.get(),
            "stage_serial_number": st1.get(),
            "operator": opName1.get(),
            "part_number": st_type1.get(),
            "temp": tem1.get(),
            "comments": comm1.get(),
            "col_axis": col1.get()
        }
        save_user_inputs(user_data)
        window.destroy()
    
    window.protocol("WM_DELETE_WINDOW", rot_on_closing)

    '''
    Tab 2: Angular Testing
    
    This tab is for running pitch, yaw, and roll tests
    '''
    # Load stored data or set defaults
    ang_test_type_value = stored_data.get("direction", '')
    ang_axis_value = stored_data.get("axis_name", "X")
    ang_start_value = stored_data.get("start_position", 0)
    ang_travel_value = stored_data.get("travel", 100)
    ang_step_value = stored_data.get("step_size", 5)
    ang_controller_value = stored_data.get("controller", '')
    ang_units_value = stored_data.get("units", '')
    ang_colx_value = stored_data.get("col_x", '')
    ang_coly_value = stored_data.get("col_y", '')
    ang_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    ang_st_value = stored_data.get("stage_serial_number", '"Stage Serial Number"')
    ang_op_value = stored_data.get("operator", '"Your Initials"')
    ang_part_value = stored_data.get("part_number", '"Part Number"')
    ang_temp_value = stored_data.get("temp", 20)
    ang_comm_value = stored_data.get("comments", "")
    
    def angular_live_plot():
        
        global xforwarddata,xreversedata,yforwarddata,yreversedata,col_axis_X,col_axis_Y
        global fig1,ax1,fig2,ax2, plot_mean
        
        plot_font = {'family': 'serif', 'weight': 'normal', 'size': 12}
        title_font = {'family': 'serif', 'weight': 'normal', 'size': 16}
        # Create a Figure and Axes for the plot
        fig1, ax1 = plt.subplots()
        ax1.set_facecolor("white")
        ax1.set_xlabel("Position", fontdict=plot_font, color='darkred')
        ax1.set_ylabel(f"{col_axis_X}", fontdict=plot_font, color='darkred')
        ax1.set_title("Angular Errors", fontdict=title_font)
        
        canvas = FigureCanvasTkAgg(fig1, master=tab2,)
        canvas.get_tk_widget().grid(row=0, column=4, rowspan=10, columnspan=3, padx=1, pady=(17,0), sticky='nsew')
        
        ax1.grid(False)
        
        fig2, ax2 = plt.subplots()
        ax2.set_facecolor("white")
        ax2.set_xlabel("Position",fontdict=plot_font, color='darkred')
        ax2.set_ylabel(f"{col_axis_Y}",fontdict=plot_font, color='darkred')
        #ax2.set_title("Angular Errors", fontdict=plot_font)
        
        canvas = FigureCanvasTkAgg(fig2, master=tab2,)
        canvas.get_tk_widget().grid(row=11, column=4, rowspan=10, columnspan=3, padx=1, pady=(7,0), sticky='nsew')
        
        ax2.grid(False)
        
        '''
        Using Queue Method
        
        
        global queue
        queue = Queue(maxsize=0)
        
        def update_plot(frame):
            if not queue.empty():
                xdata, ydata = queue.get()
    
                ax.cla()  # Clear the current plot
                ax.plot(xdata, ydata)  # Plot all the data points
                print(xdata,ydata)
                
        
        global ani
        ani = FuncAnimation(fig, update_plot, interval=100)
        '''
        def update_plot(frame):
            global xforwarddata,xreversedata,yforwarddata,yreversedata
            
            ax1.cla()  # Clear the current plot
            ax2.cla()

            ax1.plot(xforwarddata, yforwarddata, color='b', marker='o')
            ax1.plot(xreversedata, yreversedata, color='r', marker='x')# Plot all the data points
            ax2.plot(xforwarddata, zforwarddata, color='b', marker='o')
            ax2.plot(xreversedata, zreversedata, color='r', marker='x')# Plot all the data points
            ax1.relim()
            ax1.autoscale_view()
            
            ax1.set_xlabel("Position", font=plot_font)
            ax1.set_ylabel(f"{col_axis_X}", font=plot_font)
            ax1.set_title("Angular Errors", font=plot_font)
            
            ax2.set_xlabel("Position")
            ax2.set_ylabel(f"{col_axis_Y}")
            #ax2.set_title("Angular Errors", fontsize=16)
            
            # Set the font size for the tick labels
            ax1.tick_params(axis='both', which='major', labelsize=10)
            ax2.tick_params(axis='both', which='major', labelsize=10)
            
            canvas.draw()
            
        def handle_client(clientsocket):
            global yrawforward,zrawforward,yrawreverse,zrawreverse,xforwarddata,xreversedata,yforwarddata,zforwarddata,zreversedata,yreversedata,plot_mean
            while True:
                data = clientsocket.recv(1024)
                if not data:
                    break
                data = data.decode('utf-8').split(',')
                forward_fbk = None
                forwardx_data = None
                forwardy_data = None
                reversex_data = None
                reversey_data = None
                
                for item in data:
                    if "forward:" in item:
                        forward_fbk = item.split(":")[1].strip()
                        x = float(forward_fbk)
                        xforwarddata.append(x)
                    elif f"forward {col_axis_X}:" in item:
                        forwardx_data = item.split(":")[1].strip()
                        y = float(forwardx_data)
                        yrawforward.append(y)
                        plot_mean = np.mean(yrawforward)
                        #yforwarddata.append(y)
                        yforwarddata = [i - plot_mean for i in yrawforward]
                    elif f"forward {col_axis_Y}:" in item:
                        forwardy_data = item.split(":")[1].strip()
                        z = float(forwardy_data)
                        zrawforward.append(z)
                        plot_mean = np.mean(zrawforward)
                        #yforwarddata.append(y)
                        zforwarddata = [i - plot_mean for i in zrawforward]
                        break
                    
                    if "reverse" in item:
                        reverse_fbk = item.split(":")[1].strip()
                        x = float(reverse_fbk)
                        xreversedata.append(x)
                    elif f"reverse {col_axis_X}" in item:
                        reversex_data = item.split(":")[1].strip()
                        y = float(reversex_data)
                        yrawreverse.append(y)
                        plot_mean = np.mean(yrawreverse)
                        #yforwarddata.append(y)
                        yreversedata = [i - plot_mean for i in yrawreverse]
                    elif f"forward {col_axis_Y}" in item:
                        reversey_data = item.split(":")[1].strip()
                        z = float(reversey_data)
                        zrawreverse.append(z)
                        plot_mean = np.mean(zrawreverse)
                        #yforwarddata.append(y)
                        zreversedata = [i - plot_mean for i in zrawreverse]
                        break
                                            
            gc.collect()                         
            clientsocket.close()
        def run_server():
            global clientsocket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((socket.gethostname(), 1234))
            s.listen(5)
        
            while True:
                # now our endpoint knows about the OTHER endpoint.
                clientsocket, address = s.accept()
                threading.Thread(target=handle_client, args=(clientsocket,)).start()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        global ani1,ani2
        ani1 = FuncAnimation(fig1, update_plot, interval=1000,cache_frame_data=False)
        ani2 = FuncAnimation(fig2, update_plot, interval=1000,cache_frame_data=False)
        
    def angular_test_type_def():
        global test_type
        if direction.get() == "uni":
            test_type = 'Unidirectional'
        elif direction.get() == "bi":
            test_type = 'Bidirectional'
        else:
            test_type = 'None'
    
    def colaxis_def():
        global col_axis_X, col_axis_Y
        if colaxisX.get() == 'pitch':
            col_axis_X = 'Pitch'
        elif colaxisX.get() == 'yaw':
            col_axis_X = 'Yaw'
        elif colaxisX.get() == 'roll':
            col_axis_X = 'Roll'
        if colaxisY.get() == 'pitch':
            col_axis_Y = 'Pitch'
        elif colaxisY.get() == 'yaw':
            col_axis_Y = 'Yaw'
        elif colaxisY.get() == 'roll':
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
            "direction": direction.get(),
            "axis_name": ax.get(),
            "start_position": start.get(),
            "travel": trav.get(),
            "step_size": step.get(),
            "controller": con.get(),
            "units": units2.get(),
            "col_x": colaxisX.get(),
            "col_y": colaxisY.get(),
            "system_serial_number": syst.get(),
            "stage_serial_number": st.get(),
            "operator": opName.get(),
            "part_number": st_type1.get(),
            "temp": tem1.get(),
            "comments": comm1.get(),
            "col_axis": col1.get()
        }
        save_user_inputs(user_data)
        try:
            angulartest()
        finally:
            gc.collect()                         
            clientsocket.close()
            window.after(0, btn_run_ang.config, {'state': tk.NORMAL})

    def angulartest():
        axis = str(ax.get())
        start_pos = float(start.get())
        travel = float(trav.get())
        step_size = float(step.get())
        drive = str(con.get())
        units = str(units2.get())
        num_readings = 5
        dwell = 1
        sys_serial = str(syst.get())
        st_serial = str(st.get())
        oper = str(opName.get())
        stage_type = str(st_type.get())
        temp = float(tem.get())
        comments = str(comm.get())

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

        axis = ax1.get()
        sys_serial = sys1.get()

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

        axis = ax1.get()
        num_readings = 5
        dwell = 1
        step_size = float(step1.get())
        travel = float(trav1.get())
        temp = float(tem1.get())
        start_pos = float(start1.get())
        dia = diam1.get()
        sys_serial = sys1.get()
        st_serial = st1.get()
        comments = comm1.get()
        stage_type = st_type1.get()
        oper = opName1.get()

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
    
    lbl_test = tk.Label(
        master=tab2,
        text="Select Test Type:",
    )
    
    # Load stored data or set defaults
    ang_test_type_value = stored_data.get("direction", '')
    ang_axis_value = stored_data.get("axis_name", "X")
    ang_start_value = stored_data.get("start_position", 0)
    ang_travel_value = stored_data.get("travel", 100)
    ang_step_value = stored_data.get("step_size", 5)
    ang_controller_value = stored_data.get("controller", '')
    ang_units_value = stored_data.get("units", '')
    ang_colx_value = stored_data.get("col_x", '')
    ang_coly_value = stored_data.get("col_y", '')
    ang_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    ang_st_value = stored_data.get("stage_serial_number", '"Stage Serial Number"')
    ang_op_value = stored_data.get("operator", '"Your Initials"')
    ang_part_value = stored_data.get("part_number", '"Part Number"')
    ang_temp_value = stored_data.get("temp", 20)
    ang_comm_value = stored_data.get("comments", "")
    
    lbl_test.grid(row=test_row,column=0,padx=5,pady=5)
    
    direction = tk.StringVar(value=ang_test_type_value)
    
    uni_dir = tk.Radiobutton(
        master=tab2,
        text="Unidirectional",
        variable=direction,
        value="uni",
        command=angular_test_type_def
    )
    uni_dir.grid(row=test_row,column=1,padx=5,pady=5)
    
    bi_dir = tk.Radiobutton(
        master=tab2,
        text="Bidirectional",
        variable=direction,
        value="bi",
        command=angular_test_type_def
    )
    bi_dir.grid(row=test_row,column=2,padx=5,pady=5)
    
    lbl_axis = tk.Label(
        master=tab2,
        text="Axis Name",
        width=25,
        height=1,
    )
    lbl_axis.grid(row=axName_row,column=0,padx=5,pady=5)
    
    ax = tk.StringVar(value=ang_axis_value)
    ent_axis = tk.Entry(
        master=tab2,
        textvariable=ax,
        width=25,
    )
    ent_axis.grid(row=axName_row,column=1,padx=5,pady=5)
    
    lbl_st = tk.Label(
        master=tab2,
        text="Starting Position",
        width=25,
        height=1,
    )
    lbl_st.grid(row=ll_row,column=0,padx=5,pady=5)
    
    start = tk.DoubleVar(value=ang_start_value)
    ent_start_pos = tk.Entry(
        master=tab2,
        textvariable=start,
        width=25,
    )
    ent_start_pos.grid(row=ll_row,column=1,padx=5,pady=5)
    
    lbl_travel = tk.Label(
        master=tab2,
        text="Total Travel",
        width=25,
        height=1,
    )
    lbl_travel.grid(row=ul_row,column=0,padx=5,pady=5)
    
    trav = tk.DoubleVar(value=ang_travel_value)
    ent_travel = tk.Entry(
        master=tab2,
        textvariable=trav,
        width=25,
    )
    ent_travel.grid(row=ul_row,column=1,padx=5,pady=5)
    
    lbl_step_size = tk.Label(
        master=tab2,
        text="Step Size",
        width=25,
        height=1,
    )
    lbl_step_size.grid(row=ts_row,column=0,padx=5,pady=5)
    
    step = tk.DoubleVar(value=ang_step_value)
    ent_step_size = tk.Entry(
        master=tab2,
        textvariable=step,
        width=25,
    )
    ent_step_size.grid(row=ts_row,column=1,padx=5,pady=5)
    
    lbl_drive = tk.Label(
        master=tab2,
        text="Controller:",
        width=25,
        height=1
    )
    lbl_drive.grid(row=axName_row,column=2,padx=5,pady=5)
    
    # Options for the dropdown menu
    drive_options = ['Automation1', 'A3200', 'Other']
    con = tk.StringVar()
    con.set(ang_controller_value)  # Set default value
    
    cont = tk.OptionMenu(
        tab2,  # The parent widget
        con,  # The variable to hold the selected option
        *drive_options  # The options to display    
    )
    cont.grid(row=ll_row,column=2,padx=5,pady=5)
    
    lbl_units = tk.Label(
        master=tab2,
        text="Units:",
        width=25,
        height=1
    )
    lbl_units.grid(row=axName_row,column=3,padx=5,pady=5)
    
    # Options for the dropdown menu
    unit_options = ['mm', 'um', 'in','m']
    units2 = tk.StringVar()
    units2.set(ang_units_value)  # Set default value
    
    un = tk.OptionMenu(
        tab2,  # The parent widget
        units2,  # The variable to hold the selected option
        *unit_options  # The options to display
    )
    un.grid(row=ll_row,column=3,padx=5,pady=5)
    
    lbl_xdir = tk.Label(
        master=tab2,
        text = "Collimator X:",
    )
    lbl_xdir.grid(row=eq_row, column=0,padx=5,pady=5)
    
    colaxisX = tk.StringVar(value=ang_colx_value)
    cbx_xpitch = tk.Radiobutton(
        master=tab2,
        text="Pitch",
        variable=colaxisX,
        value='pitch',
        command=colaxis_def
    )
    cbx_xpitch.grid(row=eq_row,column=1,padx=5,pady=5)
    
    cbx_xyaw = tk.Radiobutton(
        master=tab2,
        text="Yaw",
        variable=colaxisX,
        value='yaw',
        command=colaxis_def
    )
    cbx_xyaw.grid(row=eq_row,column=2,padx=5,pady=5)
    
    cbx_xroll = tk.Radiobutton(
        master=tab2,
        text="Roll",
        variable=colaxisX,
        value='roll',
        command=colaxis_def
    )
    cbx_xroll.grid(row=eq_row,column=3,padx=5,pady=5)
    
    lbl_ydir = tk.Label(
        master=tab2,
        text = "Collimator Y:",
    )
    lbl_ydir.grid(row=eqa_row, column=0,padx=5,pady=5)
    
    colaxisY = tk.StringVar(value=ang_coly_value)
    cbx_ypitch = tk.Radiobutton(
        master=tab2,
        text="Pitch",
        variable=colaxisY,
        value='pitch',
        command=colaxis_def
    )
    cbx_ypitch.grid(row=eqa_row,column=1,padx=5,pady=5)
    
    cbx_yyaw = tk.Radiobutton(
        master=tab2,
        text="Yaw",
        variable=colaxisY,
        value='yaw',
        command=colaxis_def
    )
    cbx_yyaw.grid(row=eqa_row,column=2,padx=5,pady=5)
    
    cbx_yroll = tk.Radiobutton(
        master=tab2,
        text="Roll",
        variable=colaxisY,
        value='roll',
        command=colaxis_def
    )
    cbx_yroll.grid(row=eqa_row,column=3,padx=5,pady=5)
    
    lbl_serial = tk.Label(
        master=tab2,
        text="System Serial Number",
        width=25,
        height=1,
    )
    lbl_serial.grid(row=sn_row,column=0,padx=5,pady=5)
    
    syst = tk.StringVar(value=ang_sys_value)
    ent_serial = tk.Entry(
        master=tab2,
        textvariable=syst,
        width=25,
    )
    ent_serial.grid(row=sn_row,column=1,columnspan=3,padx=5,pady=5)
    
    lbl_st_serial = tk.Label(
        master=tab2,
        text="Stage Serial Number",
        width=25,
        height=1,
    )
    lbl_st_serial.grid(row=stage_row,column=0,padx=5,pady=5)
    
    st= tk.StringVar(value=ang_st_value)
    ent_st_serial = tk.Entry(
        master=tab2,
        textvariable=st,
        width=25,
    )
    ent_st_serial.grid(row=stage_row,column=1,columnspan=3,padx=5,pady=5)
    
    lbl_op = tk.Label(
        master=tab2,
        text="Operator",
        width=25,
        height=1,
    )
    lbl_op.grid(row=op_row,column=0,padx=5,pady=5)
    
    opName= tk.StringVar(value=ang_op_value)
    ent_op = tk.Entry(
        master=tab2,
        textvariable=opName,
        width=25,
    )
    ent_op.grid(row=op_row,column=1,columnspan=3,padx=5,pady=5)
    
    
    lbl_stage = tk.Label(
        master=tab2,
        text="Stage Part Number",
        width=25,
        height=1,
    )
    lbl_stage.grid(row=cv_row,column=0,padx=5,pady=5)
    
    st_type = tk.StringVar(value=ang_part_value)
    ent_stage = tk.Entry(
        master=tab2,
        textvariable=st_type,
        width=25,
    )
    ent_stage.grid(row=cv_row,column=1,columnspan=3,padx=5,pady=5)
    
    lbl_temp = tk.Label(
        master=tab2,
        text="Temp",
        width=25,
        height=1,
    )
    lbl_temp.grid(row=ol_row,column=0,padx=5,pady=5)
    
    tem = tk.DoubleVar(value=ang_temp_value)
    ent_temp = tk.Entry(
        master=tab2,
        textvariable=tem,
        width=25,
    )
    ent_temp.grid(row=ol_row,column=1,columnspan=3,padx=5,pady=5)
    
    lbl_comments = tk.Label(
        master=tab2,
        text="Comments",
        width=25,
        height=1,
    )
    lbl_comments.grid(row=pm_row,column=0,padx=5,pady=5)
    
    comm= tk.StringVar(value=ang_comm_value)
    ent_comments = tk.Entry(
        master=tab2,
        textvariable=comm,
        width=25,
    )
    ent_comments.grid(row=pm_row,column=1,columnspan=3,padx=5,pady=5)
    
    btn_import_ang = tk.Button(
        master=tab2,
        text="Import Data",
        width=30,
        height = 1,
        command=import_data_angular
    )
    btn_import_ang.grid(row=run_row,column=1,padx=5,pady=5)
    
    lbl_import_ang = tk.Label(
        master=tab2,
        text='',
        anchor='w',
    )
    
    lbl_import_ang.grid(row=run_row,column=1,padx=5,pady=5,columnspan=3)
    
    btn_run_ang = tk.Button(
        master=tab2,
        text="Run",
        width=25,
        height = 1,
        command=start_angulartest
    )
    
    btn_run_ang.grid(row=run_row,column=0,padx=5,pady=5)
    
    btn_open_ang = tk.Button(
        master=tab2,
        text="Open Plot",
        width=25,
        height = 1,
        command=open_angular_Plot
    )
    
    btn_open_ang.grid(row=run_row,column=2,padx=5,pady=5)
    
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
    
    def ang_on_closing():
        # Save user inputs before closing
        user_data = {
            "direction": direction.get(),
            "axis_name": ax.get(),
            "start_position": start.get(),
            "travel": trav.get(),
            "step_size": step.get(),
            "controller": con.get(),
            "units": units2.get(),
            "col_x": colaxisX.get(),
            "col_y": colaxisY.get(),
            "system_serial_number": syst.get(),
            "stage_serial_number": st.get(),
            "operator": opName.get(),
            "part_number": st_type1.get(),
            "temp": tem1.get(),
            "comments": comm1.get(),
            "col_axis": col1.get()
        }
        save_user_inputs(user_data)
        window.destroy()
    
    window.protocol("WM_DELETE_WINDOW", ang_on_closing)
    
    window.mainloop()

if __name__ == '__main__':
    UI()
    
