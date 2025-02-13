# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 11:21:16 2024

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
import socket
import gc

from AerotechDataCal import data_and_cal
from AerotechPDF import aerotech_PDF

sys.path.append(r"K:\10. Released Software\Systems Manufacturing Support\Shared")
#sys.path.append(r"C:\Users\tbates\Python\shared")
from Logger import TextLogger
from SerialHandler import serial_com

class rotary_cal():
    def __init__(self, axis, num_readings, dwell, step_size, travel, units, dia, test_type, sys_serial, st_serial, comments, temp, start_pos, drive, stage_type, oper, text_widget, window, **kwargs):
        self.axis = axis
        self.num_readings = num_readings
        self.dwell = dwell
        self.step_size = step_size
        self.travel = travel
        self.units = units
        self.dia = dia
        self.test_type = test_type
        self.sys_serial = sys_serial
        self.st_serial = st_serial
        self.comments = comments
        self.temp = temp
        self.start_pos = start_pos
        self.drive = drive
        self.stage_type = stage_type
        self.oper = oper
        self.text_widget = text_widget
        self.window = window

        self.is_cal = kwargs.get('is_cal', None)
        self.col_axis = kwargs.get('col_axis', None)
        
        self.text_logger = TextLogger(text_widget)
        sys.stdout = self.text_logger
        
        self.window = tk.Tk()
        self.window.withdraw()
        
        self.collecting = False
        
    def __del__(self):
        sys.stdout = sys.__stdout__    

    def start_collection(self):
        self.collecting = True
        self.collection_thread = threading.Thread(target=self.a1_test)
        self.collection_thread.start()
        
    def stop_collection(self):
        self.collecting = False
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join()  # Wait for the thread to finish
        self.collection_thread = None

    def a1_test(self, controller: a1.Controller):
        self.controller = controller
        self.Xdir, self.Ydir = [], []
        self.raw_for_pos, self.raw_rev_pos = [], []
        self.raw_forward, self.raw_reverse = [], []
        self.data = 0

        global col_reading
        col_reading = serial_com(self.dwell, self.text_widget, num_readings=self.num_readings)

        status_item_configuration = a1.StatusItemConfiguration()
        status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.DriveStatus, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, self.axis)
        self.results = self.controller.runtime.status.get_status_items(status_item_configuration)
        
        axis_status = int(self.results.axis.get(a1.AxisStatusItem.AxisStatus, self.axis).value)
        self.is_cal = (axis_status & a1.AxisStatus.CalibrationEnabled1D) == a1.AxisStatus.CalibrationEnabled1D
        
        if self.is_cal:
            verify = self.prompt_user("Calibration is enabled. Do you want to proceed (Y/N)?")
            if verify.lower() == 'y':
                self.clear_text()
                self.setup_a1_test()
            else:
                self.clear_text()
                self.prompt_user("Restart test when ready")
                return
        else:
            self.setup_a1_test()
       
    def setup_a1_test(self):
        status_item_configuration = a1.StatusItemConfiguration()
        status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.DriveStatus, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, self.axis)
        self.results = self.controller.runtime.status.get_status_items(status_item_configuration)

        self.dir_step = 0.02
        self.max_speed = self.controller.runtime.parameters.axes[self.axis].motion.maxjogspeed.value
        self.speed = self.max_speed / 2.5
        if self.speed > 30:
            self.speed = 30

        if self.units == 'mm':
            self.convert_units_to_mm()
        elif self.units == 'in':
            self.convert_units_to_in()

        drive_status = int(self.results.axis.get(a1.AxisStatusItem.DriveStatus, self.axis).value)
        is_enabled = (drive_status & a1.DriveStatus.Enabled) == a1.DriveStatus.Enabled
        if not is_enabled:
            self.controller.runtime.commands.motion.enable((self.axis))
        
        axis_status = int(self.results.axis.get(a1.AxisStatusItem.AxisStatus, self.axis).value)
        is_homed = (axis_status & a1.AxisStatus.Homed) == a1.AxisStatus.Homed
        if not is_homed:
            self.controller.runtime.commands.motion.home((self.axis))
        
        self.pos_fbk = round(self.results.axis.get(a1.AxisStatusItem.PositionFeedback, self.axis).value, 6)
        
        self.controller.runtime.commands.motion.moveabsolute([self.axis], [0], [self.speed])
        time.sleep(abs(self.pos_fbk / self.speed))
        

        align = self.prompt_user("Align Ultradex and zero Autocollimator. Press 'Enter' when ready")
        if align == ">":
            self.clear_text()
            time.sleep(2)
            self.dir_sense()
        # Clean up temporary objects
        del status_item_configuration, drive_status, axis_status

        
    def setup_a1_verification(self):
        self.raw_for_pos, self.raw_rev_pos = [], []
        self.raw_forward, self.raw_reverse = [], []
        
        status_item_configuration = a1.StatusItemConfiguration()
        status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.DriveStatus, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, self.axis)
        self.results = self.controller.runtime.status.get_status_items(status_item_configuration)
        
        axis_status = int(self.results.axis.get(a1.AxisStatusItem.AxisStatus, self.axis).value)
        if self.stage_type.startswith('HEX'):
            self.is_cal = True
        else:
            self.is_cal = (axis_status & a1.AxisStatus.CalibrationEnabled1D) == a1.AxisStatus.CalibrationEnabled1D
        
        self.clear_text()
        
        if self.is_cal:
            verify = self.prompt_user("\nCalibration is enabled. Do you want to proceed with verification (Y/N)?")
            if verify.lower() == 'y':
                self.send_data('clear', 'clear')
                self.clear_text()
                self.step_size = float(self.prompt_user("Enter verification step size."))
                self.test_type = 'Bidirectional'
                self.clear_text()
            else:
                return
        
        if self.units == 'mm':
            self.radius = self.dia / 2
            self.step_size = (self.step_size / 360) * ((2 * math.pi) * self.radius)
        elif self.units == 'in':
            self.radius = self.dia / 2
            self.step_size = ((self.step_size / 360) * ((2 * math.pi) * self.radius)) / 25.4
        
        self.pos_fbk = round(self.results.axis.get(a1.AxisStatusItem.PositionFeedback, self.axis).value, 6)
        self.controller.runtime.commands.motion.moveabsolute([self.axis], [0], [self.speed])
        time.sleep(abs(self.pos_fbk / self.speed))
        
        align = self.prompt_user("Align Ultradex and zero Autocollimator. Press 'Enter' when ready. Hit 'Esc' key to cancel")
        if align == ">":
            self.clear_text()
            time.sleep(2)
            self.uni_a1_test_loop()
        else:
            return
    
    def convert_units_to_mm(self):
        self.radius = self.dia / 2
        self.step_size = (self.step_size / 360) * ((2 * math.pi) * self.radius)
        self.travel = (self.travel / 360) * ((2 * math.pi) * self.radius)
        try:
            self.dir_step = (self.dir_step / 360) * ((2 * math.pi) * self.radius)
        except:
            pass
        self.start_pos = (self.start_pos / 360) * ((2 * math.pi) * self.radius)

    def convert_units_to_in(self):
        self.radius = self.dia / 2
        self.step_size = ((self.step_size / 360) * ((2 * math.pi) * self.radius)) / 25.4
        self.travel = ((self.travel / 360) * ((2 * math.pi) * self.radius)) / 25.4
        try:
            self.dir_step = ((self.dir_step / 360) * ((2 * math.pi) * self.radius)) / 25.4
        except:
            pass
        self.start_pos = ((self.start_pos / 360) * ((2 * math.pi) * self.radius)) / 25.4

    def dir_sense(self):
        self.controller.runtime.commands.motion.moveincremental([self.axis], [self.dir_step], [self.speed])
        
        Xavg, Yavg = col_reading.collimator_reading()
        self.Xdir.append(Xavg)
        self.Ydir.append(Yavg)
        time.sleep(3)
        
        self.controller.runtime.commands.motion.moveabsolute([self.axis], [self.start_pos], [self.speed])
        time.sleep(1)
        
        self.col_axis = 'X' if abs(self.Xdir[0]) > abs(self.Ydir[0]) else 'Y'
        
        self.uni_a1_test_loop()
    
    def uni_a1_test_loop(self):
        self.connect_to_server()
        self.send_data('clear', 'clear')
        time.sleep(5)
        pos_fbk = self.update_position_feedback()
        if pos_fbk != self.start_pos:
            self.controller.runtime.commands.motion.moveabsolute([self.axis], [self.start_pos], [self.speed])
            time.sleep((abs(self.pos_fbk - self.start_pos) / self.speed) + 3)

        self.end_point = round(self.travel, 4) + round(self.start_pos, 4) if self.units != 'deg' else round(self.travel, 0) + round(self.start_pos, 0)
        self.data_accuracy, self.for_rev, self.data_rep = [], [], []
        
        while True:
            self.update_position_feedback()
            if self.pos_fbk == self.home_pos:
                self.record_data('forward')
                self.move_incremental(self.step_size)
                time.sleep((self.step_size / self.speed) + 3)
            else:
                if self.pos_fbk <= self.end_point:
                    response = self.open_data_box()
                    if response == "OK":
                        self.record_data('forward')
                        if self.pos_fbk < self.end_point:
                            self.move_incremental(self.step_size)
                            time.sleep((self.step_size / self.speed) + 3)
                    elif response == "Cancel":
                        messagebox.showerror('Abort', 'Test Stopped')
                        break

            if self.pos_fbk == self.end_point:
                break
               
        if self.pos_fbk == self.end_point:
            if self.test_type == 'Unidirectional':
                self.a1_setup_data()
            else:
                self.bi_a1_test_loop()
        return
    
    def bi_a1_test_loop(self):
        if self.pos_fbk == self.end_point:
            self.over_travel_move()
            time.sleep((self.step_size / self.speed) + 3)
        while True:
            self.update_position_feedback()
            if self.pos_fbk >= self.start_pos:
                response = self.open_data_box()
                if response == "OK":
                    self.record_data('reverse')
                    if self.pos_fbk > self.start_pos:
                        self.move_incremental(-self.step_size)
                        time.sleep((self.step_size / self.speed) + 3)
                elif response == "Cancel":
                    tk.messagebox.showerror('Abort', 'Test Stopped')
                    break
            if self.pos_fbk == self.start_pos:
                break
        if self.pos_fbk == self.start_pos:
            self.a1_setup_data()
        return
    
    def test(self):
        self.raw_for_pos = []
        self.raw_rev_pos = []
        self.raw_forward = []
        self.raw_reverse = []
        self.data_accuracy = []
        self.for_rev = []
        self.data_rep = []
        self.data = 0
        
        if self.units == 'mm':
            self.convert_units_to_mm()
        elif self.units == 'in':
            self.convert_units_to_in()
        
        global col_reading
        col_reading = serial_com(self.dwell, self.text_widget, num_readings=self.num_readings)
        #align = self.prompt_user("Align Ultradex and zero Autocollimator. Press 'Enter' when ready. Hit 'Esc' key to cancel")
# =============================================================================
#         if align == ">":
#             self.clear_text()
#             time.sleep(2)
#             if self.units != 'deg':
#                 step_prompt = self.prompt_user(f'Copy step size for Motion Composer then hit Enter: {self.step_size}')
#                 if step_prompt == '>':
#                     self.clear_text()
#                     self.uni_test_loop()
#             else:
#                 self.uni_test_loop()
#         else:
#             return
# =============================================================================
        self.uni_test_loop()
 
    def uni_test_loop(self):
        self.num_points = (self.travel / self.step_size) 
        self.bi_num_points = ((self.travel / self.step_size) * 2)
        self.test_points = 0
        self.test_distance = self.start_pos
        self.data_accuracy, self.for_rev, self.data_rep = [], [], []
        self.end_point = self.start_pos + self.travel
        self.end_point = round(self.end_point,7)
        self.start_pos = round(self.start_pos,7)
        
        while self.test_points <= self.num_points:
            response = self.manual_data_box()
            if response == "OK":
                self.record_data('forward')
                self.move_to_next_point()
            elif response == "Cancel":
                tk.messagebox.showerror('Abort', 'Test Stopped')
                cancel='yes'
                break
        try:
            if cancel != 'yes':
                if self.test_type == "Unidirectional":
                    self.setup_data()
                else:
                    self.test_distance -= self.step_size
                    self.test_points -= 1
                    self.bi_test_loop()
            else:
                return
        except UnboundLocalError:
            if self.test_type == "Unidirectional":
                self.setup_data()
            else:
                self.test_distance -= self.step_size
                self.test_points -= 1
                self.bi_test_loop()
            
    def bi_test_loop(self):
        if self.test_points == self.num_points:
            messagebox.showinfo('Over Travel', 'Execute an over-travel move and press OK')
            self.record_data('reverse')
            self.test_points += 1
            self.test_distance -= self.step_size

        while self.test_points <= self.bi_num_points:
            response = self.manual_data_box()
            if response == "OK":
                self.record_data('reverse')                   
                self.move_to_previous_point()
            elif response == "Cancel":
                tk.messagebox.showerror('Abort', 'Test Stopped')
                cancel='yes'
                break
        try:
            if cancel != 'yes':
                self.setup_data()
            else:
                return
        except UnboundLocalError:
            self.setup_data()
            
    def a1_setup_data(self):
        self.convert_data_to_float()
        self.adjust_data_direction()
        self.for_pos_fbk = self.raw_for_pos
        self.rev_pos_fbk = self.raw_rev_pos
        self.forward = self.raw_forward
        self.reverse = self.raw_reverse
        self.post_process()

    def convert_data_to_float(self):
        try:
            self.raw_forward = [float(i) for i in self.raw_forward]
            self.raw_reverse = [float(i) for i in self.raw_reverse]
        except:
            pass
        try:
            self.forward = [float(i) for i in self.forward]
            self.reverse = [float(i) for i in self.reverse]
        except:
            pass

    def adjust_data_direction(self):
        if self.col_axis == 'X':
            if self.Xdir[0] < 0:
                self.raw_forward = [-x for x in self.raw_forward]
                self.raw_reverse = [-x for x in self.raw_reverse]
        else:
            if self.Ydir[0] < 0:        
                self.raw_forward = [-y for y in self.raw_forward]
                self.raw_reverse = [-y for y in self.raw_reverse]

    def setup_data(self):
        self.convert_data_to_float()
        self.for_pos_fbk = self.raw_for_pos
        self.rev_pos_fbk = self.raw_rev_pos
        self.forward = self.raw_forward
        self.reverse = self.raw_reverse
        self.post_process()
        
    def import_data(self):
        self.for_pos_fbk = []
        self.rev_pos_fbk = []
        self.forward = []
        self.reverse = []
        self.file_path = filedialog.askopenfilename(title="Select Data File")
        if self.file_path:
            self.data = 1
            with open(self.file_path, 'r') as file:
                lines = file.readlines()
                self.parse_file_lines(lines)
            self.post_process()
        else:
            messagebox.showerror("Abort", "No file selected.")
          
    def parse_file_lines(self, lines):
        for num, line in enumerate(lines):
            if "Calibrated" in line:
                self.is_cal = line.split(":")[1].strip()
                if self.is_cal == '0':
                    self.is_cal = None
            if line.startswith(':START'):
                lines = lines[num+1:]
                break
        data_list = [(values[0], values[1]) for line in lines if (values := line.strip().split())]
        self.extract_data_from_list(data_list)

    def extract_data_from_list(self, data_list):
        if self.test_type == 'Bidirectional':
            for i, data in enumerate(data_list):
                if i < len(data_list) / 2:
                    self.for_pos_fbk.append(data[0])
                    self.forward.append(data[1])
                else:
                    self.rev_pos_fbk.append(data[0])
                    self.reverse.append(data[1])
            self.convert_data_to_float()
        else:
            for data in data_list:
                self.for_pos_fbk.append(data[0])
                self.forward.append(data[1])
            self.for_pos_fbk = [float(i) for i in self.for_pos_fbk]
            self.forward = [float(i) for i in self.forward]

    def post_process(self):
        self.current_date = datetime.date.today()
        self.current_time = datetime.datetime.now().time()
        self.reverse = self.reverse[::-1]
        self.reverse_data = self.reverse
        self.forward_data = self.forward
        self.rev_pos_fbk = self.rev_pos_fbk[::-1]
        data_mean = np.mean(self.forward)
        self.forward = [i - data_mean for i in self.forward]
        if self.test_type == 'Bidirectional':
            self.reverse = [i - data_mean for i in self.reverse]
        self.calculate_accuracy_and_repeatability()
        self.generate_reports()
        
    def calculate_accuracy_and_repeatability(self):
        if self.test_type == "Bidirectional":
            max_forward, min_forward = max(self.forward), min(self.forward)
            max_reverse, min_reverse = max(self.reverse), min(self.reverse)
            data_max, data_min = max(max_forward, max_reverse), min(min_forward, min_reverse)
            accuracy_pk = data_max + abs(data_min)
            self.pk_pk = round(accuracy_pk, 3 if self.units == 'deg' else 8)

            rep = [abs((i) - (e)) for i, e in zip(self.forward, self.reverse)]
            rep_max, rep_min = abs(max(rep)), abs(min(rep))
            self.rep = round(max(rep_max, rep_min), 3 if self.units == 'deg' else 8)
        else:
            data_max, data_min = max(self.forward), min(self.forward)
            accuracy_pk = data_max + abs(data_min)
            self.pk_pk = round(accuracy_pk, 3 if self.units == 'deg' else 8)

    def generate_reports(self):
        common_args = {
            'test_type': self.test_type, 'sys_serial': self.sys_serial, 'st_serial': self.st_serial, 
            'current_date': self.current_date, 'current_time': self.current_time, 'axis': self.axis,
            'stage_type': self.stage_type, 'drive': self.drive, 'step_size': self.step_size, 
            'for_pos_fbk': self.for_pos_fbk, 'temp': self.temp, 'units': self.units, 
            'oper': self.oper, 'start_pos': self.start_pos, 'comments': self.comments, 
            'travel': self.travel, 'test_name': 'Rotary'
        }

        if self.drive == 'Automation1' and self.data == 0:
            status_item_configuration = a1.StatusItemConfiguration()
            status_item_configuration.axis.add(a1.AxisStatusItem.DriveStatus, self.axis)
            status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, self.axis)
            results = self.controller.runtime.status.get_status_items(status_item_configuration)
            
            self.rollovercounts = self.controller.runtime.parameters.axes[self.axis].motion.rollovercounts.value
            axis_status = int(results.axis.get(a1.AxisStatusItem.AxisStatus, self.axis).value)
            self.is_cal = (axis_status & a1.AxisStatus.CalibrationEnabled1D) == a1.AxisStatus.CalibrationEnabled1D
            
            a1_data_args = {
                **common_args, 'rev_pos_fbk': self.rev_pos_fbk, 'forward_data': self.forward_data, 'reverse_data': self.reverse_data, 
                'col_axis': self.col_axis, 'is_cal': self.is_cal, 'speed': self.speed, 'dia': self.dia
            }
            data_file = data_and_cal(**a1_data_args)
            data_file.a1_data_file(self.controller)
        elif self.drive != 'Automation1' and self.data == 0:
            a3200_data_args = {
                **common_args, 'rev_pos_fbk': self.rev_pos_fbk, 'forward_data': self.forward_data, 'reverse_data': self.reverse_data,
                'col_axis': self.col_axis, 'is_cal': self.is_cal, 'dia': self.dia
            }
            data_file = data_and_cal(**a3200_data_args)
            data_file.other_data_file()

        if self.test_type == 'Bidirectional':
            bi_pdf_args = {
                **common_args, 'rev_pos_fbk': self.rev_pos_fbk, 'forward': self.forward, 'reverse': self.reverse, 
                'pk_pk': self.pk_pk, 'rep': self.rep, 'dia': self.dia, 'is_cal': self.is_cal, 
                'data': self.data
            }
            gen_pdf = aerotech_PDF(**bi_pdf_args)
        else:
            uni_pdf_args = {
                **common_args, 'forward': self.forward, 'pk_pk': self.pk_pk, 'dia': self.dia, 
                'is_cal': self.is_cal, 'data': self.data
            }
            gen_pdf = aerotech_PDF(**uni_pdf_args)

        if self.data == 0:
            gen_pdf.rotary_pdf()
        if self.data == 1:
            import_data_args = {
                **common_args, 'rev_pos_fbk': self.rev_pos_fbk, 'forward_data': self.forward_data, 'reverse_data': self.reverse_data, 
                'col_axis': self.col_axis, 'is_cal': self.is_cal, 'data': self.data, 'file_path': self.file_path
            }
            gen_pdf.rotary_pdf()
            data_file = data_and_cal(**import_data_args)

        if self.is_cal:
            messagebox.showinfo('Test Complete', 'Test Is Complete')
        else:
            self.cal = self.open_cal_box()
            if self.cal == 'OK':
                cal_ver = data_file.make_cal_file()
                if self.stage_type.startswith('HEX'):
                    if cal_ver: 
                        self.controller.reset()
                        self.controller.runtime.commands.execute('EnableWork()', 1)
                        self.setup_a1_verification()
                elif self.drive == 'Automation1':
                    self.controller.runtime.parameters.axes[self.axis].motion.calibrationiirfilter.value=50
                    self.start_path = 'O:/'
                    self.folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(self.start_path) for dir_name in dirs if str(self.sys_serial[0:6]) in dir_name), None)
                    cal_file_path = os.path.join(self.folder_path, 'Customer Files', 'CalFiles', f'{self.sys_serial}-{self.axis}.cal')
                    with open(cal_file_path, 'r') as f:
                        contents = f.read()
                    self.controller.files.write_text(f'{self.sys_serial}-{self.axis}.cal', contents)
                    self.controller.runtime.commands.calibration.calibrationload(a1.CalibrationType.AxisCalibration1D, f'{self.sys_serial}-{self.axis}.cal')
                    self.setup_a1_verification()
            else:
                messagebox.showinfo('Test Complete', 'Test Is Complete')
                
        self.cleanup_data()
        self.cleanup_resources()

    def update_position_feedback(self):
        status_item_configuration = a1.StatusItemConfiguration()
        status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
        self.results = self.controller.runtime.status.get_status_items(status_item_configuration)
        self.pos_fbk = self.results.axis.get(a1.AxisStatusItem.PositionFeedback, self.axis).value
        self.home_pos = round(self.controller.runtime.parameters.axes[self.axis].homing.homepositionset.value, 1)
        
        if self.units == 'deg':
            self.pos_fbk = round(self.pos_fbk,1)
        else:
            self.pos_fbk = round(self.pos_fbk,4)

        #return pos_fbk
    def record_data(self, direction):
        Xavg, Yavg = col_reading.collimator_reading()
        value = Xavg if self.col_axis == 'X' else Yavg
        pos_list = self.raw_for_pos if direction == 'forward' else self.raw_rev_pos
        data_list = self.raw_forward if direction == 'forward' else self.raw_reverse
    
        data_list.append(value)
        self.for_rev.append(value)
        coldata = value

        if self.drive == 'Automation1':
            pos_list.append(self.pos_fbk)
        else:
            self.pos_fbk = self.test_distance
            pos_list.append(self.pos_fbk)
        
        self.mean_data = np.mean(self.raw_forward)
        accuracy_dat = [i - self.mean_data for i in self.for_rev]
        accuracy_pk = max(accuracy_dat) + abs(min(accuracy_dat)) if min(accuracy_dat) < 0 else max(accuracy_dat)
        self.data_accuracy.append(accuracy_pk)
        accuracy = str(round(max(self.data_accuracy), 4))
        self.display_results(f'Accuracy: {accuracy}')
        
        if self.raw_reverse:
            raw_forward = [i - self.mean_data for i in self.raw_forward]
            raw_reverse = [i - self.mean_data for i in self.raw_reverse]
            self.data_rep.extend(abs(f - r) for f, r in zip(raw_forward[::-1], raw_reverse))
            data_repeat = str(round(max(abs(max(self.data_rep)), abs(min(self.data_rep))), 4))
            self.display_results(f'Accuracy: {accuracy}\nRepeat: {data_repeat}')
        
        self.send_data(f"{direction}_fbk: {self.pos_fbk}", f"{direction}_col: {coldata}")

    def move_incremental(self, distance):
        self.controller.runtime.commands.motion.moveincremental([self.axis], [distance], [self.speed])
        time.sleep((distance / self.speed) + 3)

    def over_travel_move(self):
        self.controller.runtime.commands.motion.moveincremental([self.axis], [self.dir_step], [self.speed])
        time.sleep(0.5)
        self.controller.runtime.commands.motion.moveincremental([self.axis], [self.dir_step * -1], [self.speed])
        time.sleep(3)
        self.record_data('reverse')
        self.move_incremental(-self.step_size)

    def move_to_next_point(self):
        self.test_points += 1
        self.test_distance += self.step_size
        self.test_distance = round(self.test_distance,7)

    def move_to_previous_point(self):
        self.test_points += 1
        self.test_distance -= self.step_size
        self.test_distance = round(self.test_distance,7)

    def end_test(self):
        self.prompt_user("Restart test when ready")
        self.text_widget.unbind("<Return>")
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)

    def clear_text(self):
        self.text_widget.delete(1.0, tk.END)

    def prompt_user(self, message):
        self.text_logger.write(message)
        self.text_widget.delete(1.0, tk.END)
        return self.text_logger.read_input()

    def display_results(self, message):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)
        self.text_logger.write(message)

    def open_data_box(self):
        return self.open_message_box_template("Take Data", "Index Ultradex and click OK To Take Data")

    def manual_data_box(self):
        return self.open_message_box_template("Take Manual Data", f"Index Stage To {self.test_distance} Then Click OK To Take Data")

    def open_message_box_template(self, title, message):
        box = tk.Toplevel(self.window)
        box.title(title)
        box.configure(bg='white')
        
        # Ensure the window stays on top until it loses focus
        box.wm_attributes("-topmost", True)
        
        box.lift()
        
        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")
        label = tk.Label(box, text=message, bg='white', font=custom_font)
        label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
        
# =============================================================================
#         # Make the dialog a transient window
#         box.transient(self.window)
#         box.grab_set()
# =============================================================================
        
        def on_ok(event=None):
            box.result = "OK"
            box.destroy()

        def on_cancel(event=None):
            box.result = "Cancel"
            box.destroy()

        button_ok = tk.Button(box, text="OK", width=10, height=2, command=on_ok)
        button_ok.grid(row=1, column=0, padx=10, pady=10)

        button_cancel = tk.Button(box, text="Cancel", width=10, height=2, command=on_cancel)
        button_cancel.grid(row=1, column=1, padx=10, pady=10)

        # Bind Enter key to the OK button
        box.bind("<Return>", on_ok)

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

        # Set focus to the OK button
        box.after(10, button_ok.focus_set)
        box.result = None
        box.wait_window()

        return box.result
    
    def open_message_box(self):
        align = tk.Toplevel(self.window)
        align.title('Setup')
        align.configure(bg='white')
        
        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")
        if self.drive == 'Automation1':
            label = tk.Label(align, text="Align Ultradex and manually zero Autocollimator", bg='white', font=custom_font)
        else:
            label = tk.Label(align, text="Home Axis. Align Ultradex and manually zero Autocollimator", bg='white', font=custom_font)
        label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

        def on_ok():
            align.result = "OK"
            align.destroy()

        def on_cancel():
            align.result = "Cancel"
            align.destroy()
            self.window.focus_set()
            return "Cancel"

        button_ok = tk.Button(align, text="OK", width=10, height=2, command=on_ok)
        button_ok.grid(row=1, column=0, padx=10, pady=10)
        
        align.bind("<Return>", on_ok)  # Bind Enter key to the OK button
        
        button_cancel = tk.Button(align, text="Cancel", width=10, height=2, command=on_cancel)
        button_cancel.grid(row=1, column=1, padx=10, pady=10)
        
        screen_width = align.winfo_screenwidth()
        screen_height = align.winfo_screenheight()
        
        padding = 40
        width = label.winfo_reqwidth()
        height = label.winfo_reqheight() + button_ok.winfo_reqheight()
        
        align_width = width + padding
        align_height = height + padding
        
        x_cordinate = int((screen_width / 2) - (align_width / 2))
        y_cordinate = int((screen_height / 2) - (align_height / 2))

        align.geometry("{}x{}+{}+{}".format(align_width, align_height, x_cordinate, y_cordinate))
        align.configure(bg='white')
        
        align.focus_set()
        align.result = None
        align.wait_window()
        
        return align.result    
    
    def open_cal_box(self):
        cal = tk.Toplevel(self.window)
        cal.title('Generate Cal File')
        cal.configure(bg='white')
        
        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")
        
        label = tk.Label(cal, text="Are you generating a cal file?", bg='white', font=custom_font)
        label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
        
        def on_ok():
            cal.result = 'OK'
            cal.destroy()
        
        def on_cancel():
            cal.result = "Cancel"
            cal.destroy()
            cal.destroy()
            self.window.focus_set()
            return "Cancel"
            
        button_ok = tk.Button(cal, text="Yes", width=10, height=2, command=on_ok)
        button_ok.grid(row=2, column=0, padx=10, pady=10)
        
        cal.bind("<Return>", on_ok)  # Bind Enter key to the OK button
        
        button_cancel = tk.Button(cal, text="No", width=10, height=2, command=on_cancel)
        button_cancel.grid(row=2, column=1, padx=10, pady=10)
        
        cal.resizable(False, False)

        screen_width = cal.winfo_screenwidth()
        screen_height = cal.winfo_screenheight()

        padding = 40
        width = label.winfo_reqwidth()
        height = label.winfo_reqheight() + button_ok.winfo_reqheight()

        cal_width = width + padding
        cal_height = height + padding

        x_cordinate = int((screen_width / 2) - (cal_width / 2))
        y_cordinate = int((screen_height / 2) - (cal_height / 2))

        cal.geometry("{}x{}+{}+{}".format(cal_width, cal_height, x_cordinate, y_cordinate))
            
        cal.focus_set()
        cal.result = None
        cal.wait_window()
        
        return cal.result
    
    def connect_to_server(self, retry_count=5, delay=1):
        """
        Attempts to connect to the server with retries.
        """
        # Make sure retry_count is an integer
        #print('Connecting to server - RotaryCalTest')
        if not isinstance(retry_count, int):
            raise TypeError("retry_count must be an integer")
    
        for attempt in range(retry_count):
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((socket.gethostname(), 1234))  # Ensure the address and port are correct
                #print("Connecting to:", socket.gethostname(), "on port 1234 - RotaryCalTest")
                #print("Connected to server successfully. - RotaryCalTest")
                return self.client_socket
            except socket.error as e:
                print(f"Failed to connect to server: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
        print("Failed to connect to server after multiple attempts.")
        return None
    
    def send_data(self, x, y):
        if self.client_socket:
            message = f"{x},{y}\n".encode('utf-8')
            try:
                self.client_socket.sendall(message)
            except socket.error as e:
                print(f"Failed to send data: {e}")
                self.client_socket.close()  # Close socket on error
                self.client_socket = None
                
    def cleanup_data(self):
        self.raw_for_pos.clear()
        self.raw_rev_pos.clear()
        self.raw_forward.clear()
        self.raw_reverse.clear()
        self.for_pos_fbk = []
        self.rev_pos_fbk = []
        self.forward = []
        self.reverse = []
        self.for_rev.clear()
        self.data_accuracy.clear()
        self.data_rep.clear()
        #print("Data lists cleared to free up memory.")
        
    def cleanup_resources(self):
        # ... existing cleanup code ...
        gc.collect()  # Force garbage collection to free up memory
        #print("Garbage collection completed.")