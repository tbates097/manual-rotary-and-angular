# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 09:12:26 2024

@author: tbates
"""
import tkinter as tk
from tkinter import messagebox, font
import automation1 as a1
import math
import os

class data_and_cal:
    """
    This script will import values from A1 to use to populate Aerotech Standard Cal and data files.
    """

    def __init__(self, test_type, sys_serial, st_serial, current_date, current_time, axis, stage_type, drive, step_size, for_pos_fbk, temp, units, oper, start_pos, test_name, **kwargs):
        self.test_type = test_type
        self.sys_serial = str(sys_serial)
        self.st_serial = st_serial
        self.current_date = current_date
        self.current_time = current_time
        self.axis = axis
        self.stage_type = stage_type
        self.drive = drive
        self.step_size = step_size
        self.for_pos_fbk = for_pos_fbk
        self.temp = temp
        self.units = units
        self.oper = oper
        self.start_pos = start_pos
        self.test_name = test_name
        self.set_kwargs(kwargs)

        self.root = tk.Tk()
        self.root.withdraw()

    def set_kwargs(self, kwargs):
        self.rev_pos_fbk = kwargs.get('rev_pos_fbk', [])
        self.forward_X = kwargs.get('forward_X', [])
        self.forward_Y = kwargs.get('forward_Y', [])
        self.reverse_X = kwargs.get('reverse_X', [])
        self.reverse_Y = kwargs.get('reverse_Y', [])
        self.forward_data = kwargs.get('forward_data', [])
        self.reverse_data = kwargs.get('reverse_data', [])
        self.col_axis_X = kwargs.get('col_axis_X', '')
        self.col_axis_Y = kwargs.get('col_axis_Y', '')
        self.col_axis = kwargs.get('col_axis', '')
        self.speed = kwargs.get('speed', 0)
        self.is_cal = kwargs.get('is_cal', False)
        self.data = kwargs.get('data', 0)
        self.file_path = kwargs.get('file_path', '')
        self.dia = kwargs.get('dia','')

    def a1_data_file(self, controller: a1.Controller):
        self.controller = controller
        self.set_automation1_parameters()

        data_test_type = '1' if self.test_type == 'Bidirectional' else '0'
        self.set_file_paths('Accuracy' if not self.is_cal else 'Verification', '_Accuracy.dat' if not self.is_cal else '_Verification.dat')

        with open(self.data_file_name, 'w') as f:
            self.write_file_header(f, data_test_type)
            combined_fbk, combined_data = self.combine_data_lists()

            self.write_data_to_file(f, combined_fbk, combined_data)
            
    def other_data_file(self):
        data_test_type = '1' if self.test_type == 'Bidirectional' else '0'
        self.set_file_paths('Accuracy' if not self.is_cal else 'Verification', '_Accuracy.dat' if not self.is_cal else '_Verification.dat')
        if self.is_cal:
            self.read_existing_data_file()
        else:
            self.data_file_box()
        
        with open(self.data_file_name, 'w') as f:
            self.write_file_header(f, data_test_type)
            combined_fbk, combined_data = self.combine_data_lists()

            self.write_data_to_file(f, combined_fbk, combined_data)

    def set_automation1_parameters(self):
        status_item_configuration = a1.StatusItemConfiguration()
        status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.DriveStatus, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, self.axis)
        results = self.controller.runtime.status.get_status_items(status_item_configuration)

        self.speed = self.controller.runtime.parameters.axes[self.axis].motion.maxjogspeed.value
        self.rollovercounts = self.controller.runtime.parameters.axes[self.axis].motion.rollovercounts.value
        axis_status = int(results.axis.get(a1.AxisStatusItem.AxisStatus, self.axis).value)
        self.is_cal = (axis_status & a1.AxisStatus.CalibrationEnabled1D) == a1.AxisStatus.CalibrationEnabled1D
        self.encoder = self.get_encoder_type()
        self.absolute_offset = self.controller.runtime.parameters.axes[self.axis].feedback.auxiliaryabsolutefeedbackoffset.value
        self.counts = self.controller.runtime.parameters.axes[self.axis].units.countsperunit.value
        self.home_dir = 'CW' if int(self.controller.runtime.parameters.axes[self.axis].homing.homesetup.value) & 0x1 else 'CCW'
        self.home_offset = self.controller.runtime.parameters.axes[self.axis].homing.homeoffset.value
        self.axis_num = self.controller.runtime.parameters.axes[self.axis].axis_index
        self.data_cal = '1' if self.is_cal else '0'

    def get_encoder_type(self):
        absolute = int(self.controller.runtime.parameters.axes[self.axis].feedback.auxiliaryfeedbacktype.value)
        encoder_types = {
            1: 'IncrementalEncoderSquareWave',
            2: 'IncrementalEncoderSineWave',
            4: 'AbsoluteEncoderEnDat',
            6: 'AbsoluteEncoderSSI',
            9: 'AbsoluteEncoderBiSS'
        }
        return encoder_types.get(absolute, 'None')

    def set_file_paths(self, folder, file_suffix):
        self.start_path = ('O:/')
        self.folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(self.start_path) for dir_name in dirs if str(self.sys_serial[0:6]) in dir_name), None)
        self.data_file_path = os.path.join(self.folder_path, 'TestData', f'{self.sys_serial}-{self.axis}', folder)
        os.makedirs(self.data_file_path, exist_ok=True)
        self.data_file_name = os.path.join(self.data_file_path, f'{self.sys_serial}-{self.axis}{file_suffix}')

    def write_file_header(self, f, data_test_type):
        col_axis_str = f'{self.col_axis_X}    {self.col_axis_Y}' if self.test_name == 'Angular' else f'{self.col_axis}'
        data_test_type = '1' if self.test_type == 'Bidirectional' else '0'
        self.data_cal = '1' if self.is_cal else '0'
        self.encoder = 'Incremental' if self.drive == 'Other' else self.encoder
        f.write(
            f'JobName : {self.sys_serial}\n'
            f'DateTime : {self.current_date} {self.current_time}\n'
            f'OperatorName : {self.oper}\n'
            'LaserID : \n'
            f'StageLabel : {self.stage_type}\n'
            f'Calibrated : {self.data_cal}\n'
            'MasterStartPosition : \n'
            f'ControllerVerison : {self.drive}\n'
            'Iterations : 1\n'
            f'BiDirectional : {data_test_type}\n'
            'EncoderDirection : 1\n'
            'ConversionFactor : 1\n'
            'BacklashDistance : 0\n'
            f'CountsPerUnit : {self.counts}\n'
            'TestType : Accuracy\n'
            'OpticLocation : DEFAULT\n'
            'Payload : OPTICS\n'
            'CalibrationFile : None\n'
            'HomePositionSet : 0\n'
            'TestOrientation : Horizontal\n'
            'MotionDirection : 1\n'
            'AmplifierType : CP Rev(B) @ 10 Amps\n'
            f'MoveVelocity : {self.speed}\n'
            'MoveAcceleration : 3.33\n'
            f'DriveFeedbackType : {self.encoder}\n'
            'DriveEncoderMultiplier : 570\n'
            'FirmwareVersion : 5.6.1.8\n'
            f'StageSerialNumber : {self.st_serial}\n'
            '\n'
            'Calibration File Settings\n'
            f'AxisIndex : {self.axis_num}\n'
            f'StepSize : {self.step_size}\n'
            f'HomeDirection : {self.home_dir}\n'
            f'HomeOffset : {self.home_offset}\n'
            'LimitToLimitDistance : 0\n'
            f'RolloverCounts : {self.rollovercounts}\n'
            'MotionDirection : 1\n'
            'EncoderFamily : I\n'
            '\n'
            'Ignored\n'
            '\n'
            f'Position     {col_axis_str} Data     Temperature\n'
            ':START\n'
        )

    def combine_data_lists(self):
        reverse = self.reverse_data[::-1]
        rev_pos_fbk = self.rev_pos_fbk[::-1]

        combined_data = self.forward_data + reverse if self.test_type == 'Bidirectional' else self.forward_data
        combined_fbk = self.for_pos_fbk + rev_pos_fbk if self.test_type == 'Bidirectional' else self.for_pos_fbk

        round_func = lambda x: round(float(x), 3) if self.units == 'deg' else round(float(x), 12)
        combined_fbk = list(map(str, map(round_func, combined_fbk)))
        combined_data = list(map(str, map(round_func, combined_data)))

        return combined_fbk, combined_data

    def write_data_to_file(self, f, combined_fbk, combined_data):
        for fbk, data in zip(combined_fbk, combined_data):
            f.write(f'{fbk}     {data}     {self.temp}\n')

    def make_cal_file(self):
        self.set_cal_file_paths()
        if self.data == 1:
            self.read_existing_data_file()
        cal_data = self.get_cal_data()
        corunit = 'PRIMARY' if self.units != 'deg' else 'PRIMARY/3600'

        if self.stage_type.startswith('HEX'):
            self.create_hex_file(cal_data)
        elif self.drive == 'Automation1':
            self.create_automation1_file(cal_data, corunit)
        else:
            self.create_other_file(cal_data, corunit)

    def set_cal_file_paths(self):
        self.start_path = ('O:/')
        self.folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(self.start_path) for dir_name in dirs if str(self.sys_serial[0:6]) in dir_name), None)
        self.cal_file_path = os.path.join(self.folder_path, 'Customer Files', 'CalFiles')
        self.file_name = os.path.join(self.cal_file_path, f'{self.sys_serial}-{self.axis}.cal')

    def read_existing_data_file(self):
        data_file_path = self.folder_path + '/TestData/' + str(self.sys_serial) + '-' + str(self.axis) + '/Accuracy'
        acc_data_file_name = data_file_path + '/' + str(self.sys_serial) + '-' + str(self.axis) + '_Accuracy.dat'
        with open(acc_data_file_name, 'r') as file:
            lines = file.readlines()
            for num, line in enumerate(lines):
                if "CountsPerUnit" in line:
                    counts = line.split(":")
                    self.counts = float(counts[1].strip())
                if "AxisIndex" in line:
                    self.axis_num = line.split(":")[1].strip()
                if "HomeDirection" in line:
                    self.home_dir = line.split(":")[1].strip()
                if "HomeOffset" in line:
                    self.home_offset = line.split(":")[1].strip()
                if "RolloverCounts" in line:
                    self.rollovercounts = line.split(":")[1].strip()

    def get_cal_data(self):
        if self.units == 'mm':
            # Convert diameter to radius
            dia = float(self.dia)
            radius = dia / 2
            
            # Convert arcseconds to radians
            arcsec_to_rad = math.pi / 180 / 3600
            self.forward_data = [(i * arcsec_to_rad * radius) for i in self.forward_data]
        if self.units == 'in':
            # Convert diameter to radius
            dia = float(self.dia)
            radius = dia / 2
            
            # Convert arcseconds to radians
            arcsec_to_rad = math.pi / 180 / 3600
            self.forward_data = [((i * arcsec_to_rad * radius) / 25.4) for i in self.forward_data]
        try:
            return [-float(x) for x in self.forward_data]
        except:
            self.forward_data = [float(x) for x in self.forward_data]
            return [-x for x in self.forward_data]

    def create_hex_file(self, cal_data):
        with open(self.file_name, 'w') as f:
            f.write(f'[{self.axis}CAL]\n//Step Size in deg, correction in arc-sec\nStepSize={self.step_size}\nCorrection = {" ".join(map(str, cal_data))}')
        messagebox.showinfo('Verify Cal File', 'Copy contents of file into "...EngOnly/Hexapod/SO-1-1-kpMeasurements.txt"')

    def create_automation1_file(self, cal_data, corunit):
        self.create_cal_file(cal_data, corunit, 'AUTOMATION1')

    def create_other_file(self, cal_data, corunit):
        self.create_cal_file(cal_data, corunit, 'OTHER')
        messagebox.showinfo('Verify Cal File', 'Load cal file and re-run program to verify.')

    def create_cal_file(self, cal_data, corunit, drive_type):
        line_items = []
        data_per_line = 6

        with open(self.file_name, 'w') as f:
            self.write_cal_file_header(f, corunit, drive_type)
            for data in cal_data:
                line_items.append(f'{data}        ')
                if len(line_items) == data_per_line:
                    f.write(' '.join(line_items) + '\n')
                    line_items = []
            if line_items:
                f.write(' '.join(line_items) + '\n')
            f.write(':END')

    def write_cal_file_header(self, f, corunit, drive_type):
        if self.drive == 'Automation1':
            self.axis_num += 1
        else:
            self.axis_num = str(self.axis_num)
        header = (
            '**************************************************************************\n'
            ';***************          Aerotech Axis Calibration           **************\n'
            f';Axis System Serial Number: {self.sys_serial}-{self.axis}\n'
            f';Axis Stage Serial Number: {self.st_serial}\n'
            f';Date Tested: {self.current_date} {self.current_time}\n'
            ';Optic Location: Default\n'
            ';Payload: None\n'
            f';Average Air Temperature (°C): {self.temp}\n'
            f';CountsPerUnit Parameter: {self.counts}\n'
            '***************************************************************************\n'
            f':START {self.axis_num} SAMPLEDIST={self.step_size} POSUNIT=PRIMARY CORUNIT={corunit}\n'
            f':START OFFSET={abs(self.start_pos)}\n'
        )
    
        if drive_type == 'AUTOMATION1':
            if self.encoder in ['IncrementalEncoderSquareWave', 'IncrementalEncoderSineWave', 'None']:
                f.write(header + f':START HOMEDIRECTION={self.home_dir} HOMEOFFSET={self.home_offset}\n')
            else:
                f.write(header + f':START ABSOLUTEFEEDBACKOFFSET={self.absolute_offset}\n')
        else:
            f.write(header + f':START HOMEDIRECTION={self.home_dir} HOMEOFFSET={self.home_offset}\n')

    def a1_angular_data_file(self, controller: a1.Controller):
        self.controller = controller
        self.convert_data_to_float()
        self.set_automation1_parameters()

        data_test_type = '1' if self.test_type == 'Bidirectional' else '0'
        self.set_file_paths('Angular', '_Angular.dat')

        with open(self.data_file_name, 'w') as f:
            self.write_file_header(f, data_test_type)
            combined_fbk, combined_data = self.combine_angular_data_lists()

            self.write_angular_data_to_file(f, combined_fbk, combined_data)

    def convert_data_to_float(self):
        self.forward_X = [float(i) for i in self.forward_X]
        self.forward_Y = [float(i) for i in self.forward_Y]
        self.reverse_X = [float(i) for i in self.reverse_X]
        self.reverse_Y = [float(i) for i in self.reverse_Y]

    def combine_angular_data_lists(self):
        tab = '    '
        
        reverse_X = self.reverse_X[::-1]
        reverse_Y = self.reverse_Y[::-1]
        rev_pos_fbk = self.rev_pos_fbk[::-1]

        lists_to_round = [
            self.forward_X,
            self.forward_Y,
            reverse_X,
            reverse_Y,
            self.for_pos_fbk,
            rev_pos_fbk
        ]

        rounded_lists = [[round(i, 3) for i in lst] for lst in lists_to_round]

        combined_data = [f'{x}{tab}{y}' for x, y in zip(self.forward_X, self.forward_Y)]
        combined_fbk = self.for_pos_fbk

        if self.test_type == 'Bidirectional':
            combined_data += [f'{x}{tab}{y}' for x, y in zip(reverse_X, reverse_Y)]
            combined_fbk += rev_pos_fbk

        return combined_fbk, combined_data

    def write_angular_data_to_file(self, f, combined_fbk, combined_data):
        tab = '    '
        for fbk, data in zip(combined_fbk, combined_data):
            f.write(f'{fbk}{tab}{data}{tab}{self.temp}\n')

    def data_file_box(self):
        df = tk.Toplevel(self.root)
        df.title('Generate Data File')
        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")

        if self.drive != "Automation1":
            self.create_data_file_form(df, custom_font)
        df.focus_set()
        df.result = None
        df.wait_window()
        return df.result

    def create_data_file_form(self, df, custom_font):
        home_dir_menu, entry_fields = self.create_form_entries(df, custom_font)
        self.create_form_buttons(df, home_dir_menu, entry_fields)

        df_width, df_height = self.calculate_form_dimensions(df)
        df.geometry(f"{df_width}x{df_height}+100+200")
        df.configure(bg='white')

    def create_form_entries(self, df, custom_font):
        home_dir = ["CW", "CCW"]
        home_dir_menu = tk.StringVar(df)
        home_dir_menu.set(home_dir[1])
    
        label_texts = ["Axis Number:", "Home Direction:", "Home Offset:", "Counts Per Unit:", "Rollover Counts:", "Speed:"]
        default_values = ['1', '0', '0', '0', '0', '0']
    
        tk.Label(df, text="Input relevant data file information", bg='white', font=custom_font).grid(row=0, column=0, columnspan=2, padx=20, pady=10)
    
        entry_fields = {}
        for i, (label_text, default_value) in enumerate(zip(label_texts, default_values)):
            tk.Label(df, text=label_text, bg='white', font=custom_font).grid(row=2 * i + 1, column=0, columnspan=2, padx=10, pady=5)
            if label_text == "Home Direction:":
                tk.OptionMenu(df, home_dir_menu, *home_dir).grid(row=2 * i + 2, column=0, columnspan=2, padx=10, pady=5)
            else:
                entry = tk.Entry(df)
                entry.insert(0, default_value)
                entry.grid(row=2 * i + 2, column=0, columnspan=2, padx=10, pady=5)
                entry_fields[label_text] = entry
    
        return home_dir_menu, entry_fields

    def create_form_buttons(self, df, home_dir_menu, entry_fields):
        def on_ok():
            self.set_form_values(home_dir_menu, entry_fields)
            df.result = 'OK'
            df.destroy()

        def on_cancel():
            df.result = "Cancel"
            df.destroy()

        tk.Button(df, text="OK", width=10, height=2, command=on_ok).grid(row=13, column=0, padx=10, pady=10)
        tk.Button(df, text="Cancel", width=10, height=2, command=on_cancel).grid(row=13, column=1, padx=10, pady=10)

    def set_form_values(self, home_dir_menu, entry_fields):
        self.home_dir = home_dir_menu.get()
        self.axis_num = entry_fields["Axis Number:"].get()
        self.home_offset = entry_fields["Home Offset:"].get()
        self.counts = entry_fields["Counts Per Unit:"].get()
        self.rollovercounts = entry_fields["Rollover Counts:"].get()
        self.speed = entry_fields["Speed:"].get()

    def calculate_form_dimensions(self, df):
        width_padding = 40
        height_padding = 125

        width = max(widget.winfo_reqwidth() for widget in df.winfo_children())
        height = sum(widget.winfo_reqheight() for widget in df.winfo_children())
        return width + width_padding, height + height_padding


