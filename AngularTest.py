# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 08:44:19 2024

@author: tbates
"""

import automation1 as a1
import os
import sys
import tkinter as tk
from tkinter import messagebox, font, filedialog
import time
import math
import numpy as np
import datetime
import threading
from RS232 import collimator
from AerotechDataCal import data_and_cal
from AerotechPDF import aerotech_PDF
from Logger import TextLogger
import socket

class angular:
    '''
    Program to execute an accuracy and calibration test for a rotary stage that cannot be mounted in the Rotary Calibrator.
    This program will automate motion of the test and master axis and collect autocollimator data.
    It will then post-process and make plots with a calibration file.
    '''

    def __init__(self, test_type, axis, start_pos, travel, step_size, col_axis_X, col_axis_Y, drive, units, sys_serial, st_serial, oper, stage_type, temp, comments, num_readings, dwell, text_widget, window, **kwargs):
        self.test_type = test_type
        self.axis = axis
        self.start_pos = start_pos
        self.travel = travel
        self.step_size = step_size
        self.col_axis_X = col_axis_X
        self.col_axis_Y = col_axis_Y
        self.drive = drive
        self.units = units
        self.sys_serial = sys_serial
        self.st_serial = st_serial
        self.oper = oper
        self.stage_type = stage_type
        self.temp = temp
        self.comments = comments
        self.num_readings = num_readings
        self.dwell = dwell
        self.text_widget = text_widget
        self.window = window

        self.text_logger = TextLogger(text_widget)
        sys.stdout = self.text_logger

        self.root = tk.Tk()
        self.root.withdraw()

        self.collecting = False

    def a1_test(self, controller: a1.Controller):
        self.controller = controller
        self.initialize_test_variables()

        global col_reading
        col_reading = collimator(self.num_readings, self.dwell, self.text_widget)

        status_item_configuration = a1.StatusItemConfiguration()
        status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.DriveStatus, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, self.axis)
        self.results = self.controller.runtime.status.get_status_items(status_item_configuration)

        self.speed = self.controller.runtime.parameters.axes[self.axis].motion.maxjogspeed.value

        self.setup_a1_test()

    def initialize_test_variables(self):
        self.Xdir = []
        self.Ydir = []
        self.raw_for_pos = []
        self.raw_rev_pos = []
        self.raw_forward_X = []
        self.raw_reverse_X = []
        self.raw_forward_Y = []
        self.raw_reverse_Y = []
        self.data = 0

    def setup_a1_test(self):
        self.convert_units_to_mm()

        drive_status = int(self.results.axis.get(a1.AxisStatusItem.DriveStatus, self.axis).value)
        if not (drive_status & a1.DriveStatus.Enabled):
            self.controller.runtime.commands.motion.enable((self.axis))

        axis_status = int(self.results.axis.get(a1.AxisStatusItem.AxisStatus, self.axis).value)
        if not (axis_status & a1.AxisStatus.Homed):
            self.controller.runtime.commands.motion.home((self.axis))

        self.pos_fbk = round(self.results.axis.get(a1.AxisStatusItem.PositionFeedback, self.axis).value, 6)
        self.controller.runtime.commands.motion.moveabsolute([self.axis], [0], [self.speed])
        time.sleep(abs(self.pos_fbk / self.speed))

        if self.prompt_user("Manually zero Autocollimator. Press 'Enter' when ready. Hit 'Esc' key to cancel") == ">":
            self.clear_text()
            time.sleep(2)
            self.uni_a1_test_loop()

    def convert_units_to_mm(self):
        unit_conversion = {'um': 1000, 'in': 25.4, 'm': 1000, 'mm': 1}
        factor = unit_conversion.get(self.units, 1)

        self.step_size *= factor
        self.travel *= factor
        self.start_pos *= factor

    def uni_a1_test_loop(self):
        self.connect_to_server()
        self.move_to_start_pos()
        self.end_point = round(self.travel, 4) + round(self.start_pos, 4) if self.units in ['in', 'm'] else round(self.travel, 0) + round(self.start_pos, 0)
        if self.units == 'mm':
            self.rounding = 0
        else:
            self.rounding = 4
        self.initialize_test_results()

        while True:
            self.update_position_feedback()
            self.collect_and_process_data('forward')
            if round(self.pos_fbk,self.rounding) == self.end_point:
                break
            
            self.controller.runtime.commands.motion.moveincremental([self.axis], [self.step_size], [self.speed])
            time.sleep((self.step_size / self.speed) + 3)

        if self.test_type == 'Unidirectional':
            self.post_process()
        else:
            self.bi_a1_test_loop()

    def bi_a1_test_loop(self):
        data_rep_X, data_rep_Y = [], []
        while True:
            self.update_position_feedback()
            self.collect_and_process_data('reverse')

            reverse_X = [i - self.mean_X for i in self.for_rev_X]
            reverse_Y = [i - self.mean_Y for i in self.for_rev_Y]
            self.data_accuracy_X.append(self.calculate_accuracy(reverse_X))
            self.data_accuracy_Y.append(self.calculate_accuracy(reverse_Y))

            self.accuracy_X = str(round(max(self.data_accuracy_X), 4))
            self.accuracy_Y = str(round(max(self.data_accuracy_Y), 4))

            difference_X = abs(self.raw_forward_X[-1]) - abs(self.raw_reverse_X[0])
            difference_Y = abs(self.raw_forward_Y[-1]) - abs(self.raw_reverse_Y[0])
            data_rep_X.append(difference_X)
            data_rep_Y.append(difference_Y)

            self.data_repeat_X = str(self.calculate_repeatability(data_rep_X))
            self.data_repeat_Y = str(self.calculate_repeatability(data_rep_Y))

            self.display_results(f'{self.col_axis_X} Accuracy: {self.accuracy_X}\n{self.col_axis_Y} Accuracy: {self.accuracy_Y}\n{self.col_axis_X} Repeat: {self.data_repeat_X}\n{self.col_axis_Y} Repeat: {self.data_repeat_Y}')
            
            if round(self.pos_fbk,self.rounding) == self.end_point:
                break
            
            self.controller.runtime.commands.motion.moveincremental([self.axis], [self.step_size], [self.speed])
            time.sleep((self.step_size / self.speed) + 3)

        self.post_process()

    def move_to_start_pos(self):
        if self.pos_fbk != self.start_pos:
            self.controller.runtime.commands.motion.moveabsolute([self.axis], [self.start_pos], [self.speed])
            time.sleep((abs(self.pos_fbk - self.start_pos) / self.speed) + 3)

    def initialize_test_results(self):
        self.for_rev_X = []
        self.for_rev_Y = []
        self.data_accuracy_X = []
        self.data_accuracy_Y = []

    def update_position_feedback(self):
        status_item_configuration = a1.StatusItemConfiguration()
        status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
        self.results = self.controller.runtime.status.get_status_items(status_item_configuration)
        self.pos_fbk = round(self.results.axis.get(a1.AxisStatusItem.PositionFeedback, self.axis).value, 6)

    def collect_and_process_data(self, direction):
        Xavg, Yavg = col_reading.collimator_reading()
        self.record_data(direction, Xavg, Yavg)

    def record_data(self, direction, Xavg, Yavg):
        pos_list = self.raw_for_pos if direction == 'forward' else self.raw_rev_pos
        data_X = self.raw_forward_X if direction == 'forward' else self.raw_reverse_X
        data_Y = self.raw_forward_Y if direction == 'forward' else self.raw_reverse_Y

        data_X.append(Xavg)
        data_Y.append(Yavg)
        self.for_rev_X.append(Xavg)
        self.for_rev_Y.append(Yavg)
        pos_list.append(self.pos_fbk)

        self.mean_X = np.mean(self.raw_forward_X)
        self.mean_Y = np.mean(self.raw_forward_Y)

        coldataX = f"{direction} {self.col_axis_X}: {Xavg}"
        coldataY = f"{direction} {self.col_axis_Y}: {Yavg}"
        datafbk = f"{direction}: {self.pos_fbk}"

        self.send_data(datafbk, coldataX, coldataY)

        forward_X = [i - self.mean_X for i in self.for_rev_X]
        forward_Y = [i - self.mean_Y for i in self.for_rev_Y]
        self.data_accuracy_X.append(self.calculate_accuracy(forward_X))
        self.data_accuracy_Y.append(self.calculate_accuracy(forward_Y))

        self.accuracy_X = str(round(max(self.data_accuracy_X), 4))
        self.accuracy_Y = str(round(max(self.data_accuracy_Y), 4))

        self.display_results(f'{self.col_axis_X}: {self.accuracy_X}, {self.col_axis_Y}: {self.accuracy_Y}')

    def calculate_accuracy(self, data):
        data_min, data_max = min(data), max(data)
        return data_max + abs(data_min) if data_min < 0 and data_max > 0 else data_max

    def calculate_repeatability(self, data):
        return round(max(abs(max(data)), abs(min(data))), 4)

    def post_process(self):
        self.prepare_data_for_processing()
        
        # Generate data file based on the drive type
        if self.data == 0:
            self.generate_data_file()
        
        # Generate report PDF based on the test type
        self.generate_report()
    
        messagebox.showinfo('Test Complete', 'Test Is Complete')

    def prepare_data_for_processing(self):
        # Prepares and organizes data for further processing
        self.raw_forward_X = [float(i) for i in self.raw_forward_X]
        self.raw_reverse_Y = [float(i) for i in self.raw_reverse_Y]
    
        self.for_pos_fbk = list(self.raw_for_pos)
        self.rev_pos_fbk = list(self.raw_rev_pos)
        self.forward_X = list(self.raw_forward_X)
        self.forward_Y = list(self.raw_forward_Y)
        self.reverse_X = list(self.raw_reverse_X)
        self.reverse_Y = list(self.raw_reverse_Y)
    
        self.current_date = datetime.date.today()
        self.current_time = datetime.datetime.now().time()
    
        self.pk_pk_X = self.accuracy_X
        self.pk_pk_Y = self.accuracy_Y
        if self.test_type == "Bidirectional":
            self.rep_X = self.data_repeat_X
            self.rep_Y = self.data_repeat_Y
        self.test_name = 'Angular'
    
        # Common arguments used across data file and PDF generation
        self.common_args = {
            'test_type': self.test_type,
            'sys_serial': self.sys_serial,
            'st_serial': self.st_serial,
            'current_date': self.current_date,
            'current_time': self.current_time,
            'axis': self.axis,
            'stage_type': self.stage_type,
            'drive': self.drive,
            'step_size': self.step_size,
            'for_pos_fbk': self.for_pos_fbk,
            'temp': self.temp,
            'units': self.units,
            'oper': self.oper,
            'start_pos': self.start_pos,
            'comments': self.comments,
            'travel': self.travel,
            'test_name': self.test_name
        }
    
    def generate_data_file(self):
        if self.drive == 'Automation1':
            status_item_configuration = a1.StatusItemConfiguration()
            status_item_configuration.axis.add(a1.AxisStatusItem.DriveStatus, self.axis)
            status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, self.axis)
            results = self.controller.runtime.status.get_status_items(status_item_configuration)
    
            self.rollovercounts = self.controller.runtime.parameters.axes[self.axis].motion.rollovercounts.value
            axis_status = int(results.axis.get(a1.AxisStatusItem.AxisStatus, self.axis).value)
            self.is_cal = (axis_status & a1.AxisStatus.CalibrationEnabled1D) == a1.AxisStatus.CalibrationEnabled1D
    
            a1_data_args = {**self.common_args,
                            'rev_pos_fbk': self.rev_pos_fbk,
                            'forward_X': self.forward_X,
                            'forward_Y': self.forward_Y,
                            'reverse_X': self.reverse_X,
                            'reverse_Y': self.reverse_Y,
                            'col_axis_X': self.col_axis_X,
                            'col_axis_Y': self.col_axis_Y,
                            'speed': self.speed}
    
            data_file = data_and_cal(**a1_data_args)
            data_file.a1_angular_data_file(self.controller)
    
        else:
            a3200_data_args = {**self.common_args,
                               'rev_pos_fbk': self.rev_pos_fbk,
                               'reverse_X': self.reverse_X,
                               'reverse_Y': self.reverse_Y,
                               'col_axis_X': self.col_axis_X,
                               'col_axis_Y': self.col_axis_Y}
    
            data_file = data_and_cal(**a3200_data_args)
            data_file.angular_data_file()
    
    def generate_report(self):
        if self.test_type == 'Bidirectional' and self.data == 0:
            bi_pdf_args = {**self.common_args,
                           'rev_pos_fbk': self.rev_pos_fbk,
                           'forward_X': self.forward_X,
                           'forward_Y': self.forward_Y,
                           'reverse_X': self.reverse_X,
                           'reverse_Y': self.reverse_Y,
                           'for_rev': self.for_rev,
                           'pk_pk_X': self.pk_pk_X,
                           'pk_pk_Y': self.pk_pk_Y,
                           'rep_X': self.rep_X,
                           'rep_Y': self.rep_Y,
                           'data': self.data}
    
            gen_pdf = aerotech_PDF(**bi_pdf_args)
            gen_pdf.angular_pdf()
        elif self.test_type == 'Unidirectional' and self.data == 0:
            uni_pdf_args = {**self.common_args,
                            'forward_X': self.forward_X,
                            'forward_Y': self.forward_Y,
                            'pk_pk_X': self.pk_pk_X,
                            'pk_pk_Y': self.pk_pk_Y,
                            'data': self.data}
    
            gen_pdf = aerotech_PDF(**uni_pdf_args)
            gen_pdf.angular_pdf()
            
        elif self.data == 1:
            import_data_args = {**self.common_args,
                                'rev_pos_fbk': self.rev_pos_fbk,
                                'reverse_X': self.reverse_X,
                                'reverse_Y': self.reverse_Y,
                                'col_axis_X': self.col_axis_X,
                                'col_axis_Y': self.col_axis_Y,
                                'data': self.data,
                                'file_path': self.file_path}
    
            gen_pdf.angular_pdf()
            data_file = data_and_cal(**import_data_args)


    def end_test(self):
        self.prompt_user("Restart test when ready")
        self.clear_text()

    def clear_text(self):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)

    def prompt_user(self, message):
        self.text_logger.write(message)
        self.text_widget.delete(1.0, tk.END)
        return self.text_logger.read_input()

    def display_results(self, message):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)
        self.text_logger.write(message)

    def open_message_box(self, title, message, ok_text="OK", cancel_text="Cancel"):
        box = tk.Toplevel(self.window)
        box.title(title)
        box.configure(bg='white')

        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")
        label = tk.Label(box, text=message, bg='white', font=custom_font)
        label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

        def on_ok():
            box.result = "OK"
            box.destroy()

        def on_cancel():
            box.result = "Cancel"
            box.destroy()

        button_ok = tk.Button(box, text=ok_text, width=10, height=2, command=on_ok)
        button_ok.grid(row=1, column=0, padx=10, pady=10)

        button_cancel = tk.Button(box, text=cancel_text, width=10, height=2, command=on_cancel)
        button_cancel.grid(row=1, column=1, padx=10, pady=10)

        box.resizable(False, False)

        screen_width = box.winfo_screenwidth()
        screen_height = box.winfo_screenheight()

        padding = 40
        width = label.winfo_reqwidth()
        height = label.winfo_reqheight() + button_ok.winfo_reqheight()

        box_width = width + padding
        box_height = height + padding

        x_cordinate = int((screen_width / 2) - (box_width / 2))
        y_cordinate = int((screen_height / 2) - (box_height / 2))

        box.geometry("{}x{}+{}+{}".format(box_width, box_height, x_cordinate, y_cordinate))
        box.focus_set()
        box.result = None
        box.wait_window()

        return box.result

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((socket.gethostname(), 1234))
        print("Connected to server")

    def send_data(self, x, y, z):
        message = f"{x},{y},{z}\n".encode('utf-8')
        self.client_socket.sendall(message)

    # Re-implemented as methods
    def open_data_box(self):
        return self.open_message_box('Take Data', 'Index Ultradex and click OK To Take Data')

    def manual_data_box(self):
        return self.open_message_box('Take Manual Data', f'Index Stage To {self.test_distance} Then Click OK To Take Data')

    def open_cal_box(self):
        return self.open_message_box('Generate Cal File', 'Are you generating a cal file?', ok_text="Yes", cancel_text="No")

    def open_ver_box(self):
        return self.open_message_box('Calibration Verification', 'Verification Interval:', ok_text="OK", cancel_text="Cancel")
