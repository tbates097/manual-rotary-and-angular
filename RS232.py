# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 11:17:45 2024

@author: tbates
"""

import sys
import serial
import tkinter as tk
from tkinter import messagebox
import numpy as np
from Logger import TextLogger

class collimator():
    
    def __init__(self,num_readings,dwell,text_widget):
       '''
       Defines parameters to initialize collimator reading.

       Parameters
       ----------
       num_readings : int
           The number of readings to take that will then be averaged for a final reading.
       dwell : int
           The amount of time for the stage to settle before taking data.

       Returns
       -------
       None.

       '''
       #Initialize variables 
       self.num_readings = num_readings
       self.dwell = dwell
       self.text_widget = text_widget
       
       self.text_logger = TextLogger(text_widget)
       sys.stdout = self.text_logger
       
       #Window for error messageboxes
       self.root=tk.Tk()
       self.root.withdraw()
       
       #Close the com port
       #self.ser.close()
       
    def collimator_reading(self):
        """
        Takes multiple readings from the autocollimator and produces an average reading over the duration. Number of readings can be defined in the UI.
        
    
        Returns
        -------
        Xavg: An average of the X readings taken over the specified duration
        
        Yavg: An average of the Y readings taken over the specified duration
    
        """
        
    
        try:
            self.reading = 1
            self.Xvalues = []
            self.Yvalues = []
            
            #Start a loop that takes a collimator reading for the specified number of readings.
            while self.reading <= self.num_readings:
                self.reading = self.reading+1
                # Open serial port
                self.ser = serial.Serial('COM1', baudrate=19200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=self.dwell)  # Adjust 'COM1' to your COM port
            
                # Write command to the serial port
                self.ser.write(b'r\x0D')
            
                # Read response from the serial port
                data = self.ser.readline().decode().strip()
                response = data.split()
                if response:
                    #Take data from autocollimator through RS232 port
                    measurement_type = response[0]
    
                    status = response[1]
                    self.vx = float(response[2])
                    self.vy = float(response[3])
    
                    self.Xvalues.append(self.vx)
                    self.Yvalues.append(self.vy)
                else:
                    #Display messagebox for no data condition, close the serial port, and end the program.
                    messagebox.showerror('Collimator Error', 'No Signal From Autocollimator.')
                    self.root.destroy()
                    self.ser.close()
                    self.end_test()
                    break
                
                self.ser.close()
            
            if len(self.Xvalues) == self.num_readings:
                #Average X and Y values as a returnable variable
                Xavg = np.average(self.Xvalues, axis=None)
                Yavg = np.average(self.Yvalues, axis=None)
                self.Xavg = str(round(Xavg,3))
                self.Yavg = str(round(Yavg,3))
            else:
                pass
    
        except serial.SerialException as e:
            messagebox.showerror("Serial communication error:", e)
            self.root.destroy()

        except KeyboardInterrupt:
            messagebox.showerror("Stop Issued","Stop Issued. Ending Program")
            self.root.destroy()

        if 'ser' in locals():
            self.ser.close()
        
        return(Xavg,Yavg)
    
    def end_test(self):
        self.prompt_user("Correct issues and restart test.")
        
    def prompt_user(self, message):
        self.text_logger.write(message)
        return self.text_logger.read_input()