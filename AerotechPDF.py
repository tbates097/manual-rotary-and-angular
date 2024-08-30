# -*- coding: utf-8 -*-
"""
Created on Tue May 14 12:31:52 2024

@author: tbates
"""

import os
import numpy as np
import tkinter as tk
import math
from AerotechFormat import AerotechFormat
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

class aerotech_PDF():
    def __init__(self, test_type, sys_serial, st_serial, current_date, current_time, axis, stage_type, drive, step_size, for_pos_fbk, temp, units, comments, travel, start_pos, oper, **kwargs):
        self.test_type = test_type
        self.sys_serial = sys_serial
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
        self.comments = comments
        self.travel = travel
        self.start_pos = start_pos
        self.oper = oper
        
        # Establish kwargs
        self.forward = kwargs.get('forward', None)
        self.reverse = kwargs.get('reverse', None)
        self.forward_X = kwargs.get('forward_X', None)
        self.forward_Y = kwargs.get('forward_Y', None)
        self.reverse_X = kwargs.get('reverse_X', None)
        self.reverse_Y = kwargs.get('reverse_Y', None)
        self.rev_pos_fbk = kwargs.get('rev_pos_fbk', None)
        self.for_rev = kwargs.get('for_rev', None)
        self.pk_pk = kwargs.get('pk_pk', None)
        self.pk_pk_X = kwargs.get('pk_pk_X', None)
        self.pk_pk_Y = kwargs.get('pk_pk_Y', None)
        self.dia = kwargs.get('dia', None)
        self.is_cal = kwargs.get('is_cal', None)
        self.rep = kwargs.get('rep', None)
        self.rep_X = kwargs.get('rep_X', None)
        self.rep_Y = kwargs.get('rep_Y', None)
        self.data = kwargs.get('data', None)

        # Window for error messageboxes
        self.root = tk.Tk()
        self.root.withdraw()
    
    def rotary_pdf(self):
        self.start_path = ('O:/')
        self.sys_serial = str(self.sys_serial)
        self.folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(self.start_path) for dir_name in dirs if str(self.sys_serial[0:6]) in dir_name), None)

        # This cell of the script will be used to generate a pdf in the AerotechFooter Format
        #global fig
    
        title_font = fm.FontProperties(family='Times New Roman', size=12, weight='bold')
        label_font = fm.FontProperties(family='Times New Roman', size=10, style='italic')
        #plt.rcParams.update({'font.size': 10})
        fig, ax1, ax2, ax3, ax4 = AerotechFormat.makeTemplate()
        
        ax1 = plt.subplot2grid((19, 3),(3,0), rowspan = 8, colspan = 3,)
        plt.title('Accuracy', fontproperties=title_font)
    
        #Accuracy plot
        plt.ylabel('Accuracy (arcsec)',fontproperties=label_font)
        plt.xlabel('Position ({})'.format(self.units),fontproperties=label_font)
        if self.test_type == "Bidirectional":
            ax1.plot(self.for_pos_fbk, self.forward, '-b', label='Forward', marker='o')
            ax1.plot(self.for_pos_fbk, self.reverse, '-r', label='Reverse', marker='x')
            plt.legend(loc='upper right')
        else:
            ax1.plot(self.for_pos_fbk, self.forward, '-b', label='Accuracy', marker='o')
            plt.legend(loc='upper right')

        #Results Text Box
        if self.units == "deg":
            if self.test_type != "Bidirectional":
                ax2.text(0.02,.8, 'Accuracy: {} arcsec'.format(round(self.pk_pk,3)), color = 'black', size = 8.5)
            else:
                ax2.text(0.02,.8, 'Accuracy: {} arcsec'.format(round(self.pk_pk,3)), color = 'black', size = 8.5)
                ax2.text(0.02,.725, 'Repeat: {} arcsec'.format(round(self.rep,3)), color = 'black', size = 8.5)    
        else:
            if self.test_type != "Bidirectional":
                if self.units == 'mm':
                    radius = self.dia / 2
                    linear_pk_pk = (self.pk_pk / 360) * ((2 * math.pi) * (radius))
                else:
                    radius = self.dia / 2
                    linear_pk_pk = ((self.pk_pk / 360) * ((2 * math.pi) * (radius))) / 25.4
                #ax2.text(0.02,.725, '          {} {}'.format(round(self.pk_pk,6),self.units), color = 'black', size = 8.5)
                ax2.text(0.02,.8, 'Accuracy: {} arcsec ({} {})'.format(round(self.pk_pk,3),round(linear_pk_pk,8),self.units), color = 'black', size = 8.5)
            else:
                if self.units == 'mm':
                    radius = self.dia / 2
                    linear_pk_pk = (self.pk_pk / 360) * ((2 * math.pi) * (radius))
                    linear_rep = (self.rep / 360) * ((2 * math.pi) * (radius))
                else:
                    radius = self.dia / 2
                    linear_pk_pk = ((self.pk_pk / 360) * ((2 * math.pi) * (radius))) / 25.4
                    linear_rep = ((self.rep / 360) * ((2 * math.pi) * (radius))) / 25.4
                #ax2.text(0.02,.725, '          {} {}'.format(str(round(self.pk_pk,6)),self.units), color = 'black', size = 8.5)
                ax2.text(0.02,.8, 'Accuracy: {} arcsec ({} {})'.format(round(self.pk_pk,3),round(linear_pk_pk,8),self.units), color = 'black', size = 8.5)
                #ax2.text(0.02,.725, 'Repeatability: {} {}'.format(str(round(self.rep,6)),self.units), color = 'black', size = 8.5)
                ax2.text(0.02,.725, 'Repeat: {} arcsec ({} {})'.format(round(self.rep,3),round(linear_rep,8),self.units), color = 'black', size = 8.5)
        #Comments Text Box
        ax3.text(0.02, .8, 'System Serial Number: {}'.format(str(self.sys_serial) + '-' + str(self.axis)), color = 'black', size = 9)
        ax3.text(0.02, .725, 'Stage Serial Number: {}'.format(self.st_serial), color = 'black', size = 9)
        ax3.text(0.02, .65, 'Stage: {}'.format(self.stage_type),color='black',size=9)
        ax3.text(0.02, .575, 'Date: {} {}'.format(self.current_date,self.current_time), color = 'black', size= 9)
        ax3.text(0.02, .500, 'Operator: {}'.format(self.oper), color = 'black', size= 9)
        ax3.text(0.02, .275, 'Comments: {}'.format(self.comments), color = 'black', size = 10, verticalalignment = 'top')

        if self.is_cal:
            pdf_cal = 'Calibrated'
        else:
            pdf_cal = 'Uncalibrated'

        #Test Conditions Text Box
        degree_sign = u'\N{DEGREE SIGN}'
        ax4.text(.02, .8, 'Temperature: {} {}C'.format(self.temp, degree_sign), color = 'black', size = 9)
        ax4.text(.02, .725, 'Calibration Status: {}'.format(pdf_cal),color='black',size=9)
        ax4.text(.02, .65, 'Step Size: {} {}'.format(round(self.step_size,6),self.units), color = 'black', size = 9)
        ax4.text(.02, .575, 'Travel: {} {}'.format(round(self.travel,6), self.units), color = 'black', size = 9)
        ax4.text(.02, .500, 'Start Position: {} {}'.format(self.start_pos, self.units), color = 'black', size = 9)
        if self.units != 'deg':
            ax4.text(.02, 0.425, 'Working Diameter: {} mm'.format(self.dia), color = 'black', size = 9)

        if self.is_cal:
            output_file = str(self.sys_serial + '-' + self.axis + "_Verification.pdf")
        else:
            output_file = str(self.sys_serial + '-' + self.axis + "_Accuracy.pdf")
                
        pdf_file_path = self.folder_path + '/Customer Files/Plots'
        save_file = pdf_file_path + '/' + output_file
        fig.get_figure().savefig(save_file)
        
        self.rotary_plotly()
        
    def rotary_plotly(self):
        self.start_path = ('O:/')
        self.sys_serial = str(self.sys_serial)
        self.folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(self.start_path) for dir_name in dirs if str(self.sys_serial[0:6]) in dir_name), None)
        
        
        # This cell of the script will be used to generate a pdf in the AerotechFooter Format
        #global fig
        for attr in ['pk_pk']:
            setattr(self, attr, float(getattr(self, attr)))


        #Center data about zero for plotting
        mean_forward = np.mean(self.forward)
        
        forward = self.forward - mean_forward
        
        if self.test_type == 'Bidirectional':
            reverse = self.reverse - mean_forward
            for attr in ['rep']:
                setattr(self, attr, float(getattr(self, attr)))
        
        # Create the figure with subplots
        fig = make_subplots(
            rows=2, cols=3,
            row_heights=[1.5, 0.5],
            vertical_spacing=0.1,
            specs=[[{"type": "scatter", "colspan": 3}, None, None],
                   [{"type": "table"}, {"type": "table"}, {"type": "table"}]]
        )
        
        # Add image
        fig.add_layout_image(
            dict(
                source="AerotechLogo.png",
                xref="paper", yref="paper",
                x=0.2, y=0.4,
                sizex=0.2, sizey=0.2,
                xanchor="center", yanchor="top"
            )
        )

        # Accuracy plot
        accuracy_trace = go.Scatter(x=self.for_pos_fbk, y=forward, mode='lines+markers', name='Forward', marker=dict(color='blue'))
        fig.add_trace(accuracy_trace, row=1, col=1)

        if self.test_type == "Bidirectional":
            reverse_trace = go.Scatter(x=self.for_pos_fbk, y=reverse, mode='lines+markers', name='Reverse', marker=dict(color='red'))
            fig.add_trace(reverse_trace, row=1, col=1)

        fig.update_xaxes(title_text=f"Position ({self.units})", showline=True, linewidth=2, linecolor='black', ticks="outside", showgrid=False, zeroline=False, row=1, col=1)
        fig.update_yaxes(title_text="Accuracy (arcsec)", showline=True, linewidth=2, linecolor='black', ticks="outside", showgrid=False, zeroline=False, row=1, col=1)
        
        # Results Text Box
        results_text = ""
        if self.test_type != "Bidirectional":
            results_text = f'Accuracy: {self.pk_pk} arcsec'
        else:
            results_text = f'Accuracy: {self.pk_pk} arcsec<br>Repeat: {self.rep} arcsec'
                    
        fig.add_trace(go.Table(
            header=dict(values=["Results"], align='left'),
            cells=dict(values=[results_text.split('<br>')], align='left')), row=2, col=1)
        
        # Comments Text Box
        comments = [
            ['System Serial Number', f'{str(self.sys_serial)}-{str(self.axis)}'],
            ['Stage Serial Number', self.st_serial],
            ['Stage', self.stage_type],
            ['Date', f'{self.current_date} {self.current_time}'],
            ['Operator', self.oper],
            ['Comments', self.comments]
        ]
        comments_trace = go.Table(
            header=dict(values=["Field", "Value"], align="left"),
            cells=dict(values=[list(x) for x in zip(*comments)], align="left")
        )
        fig.add_trace(comments_trace, row=2, col=2)
    
        # Test Conditions Text Box
        pdf_cal = 'Calibrated' if self.is_cal else 'Uncalibrated'
        degree_sign = u'\N{DEGREE SIGN}'
        conditions = [
            ['Temperature', f'{self.temp} {degree_sign}C'],
            ['Calibration Status', pdf_cal],
            ['Step Size', f'{round(self.step_size, 6)} {self.units}'],
            ['Travel', f'{round(self.travel, 6)} {self.units}'],
            ['Start Position', f'{self.start_pos} {self.units}']
        ]
        if self.units != 'deg':
            conditions.append(['Working Diameter', f'{self.dia} mm'])
        conditions_trace = go.Table(
            header=dict(values=["Condition", "Value"], align="left"),
            cells=dict(values=[list(x) for x in zip(*conditions)], align="left")
        )
        fig.add_trace(conditions_trace, row=2, col=3)
        
# =============================================================================
#         # Results Text Box
#         results_text = ""
#         if self.test_type != "Bidirectional":
#             results_text = f'Accuracy: {self.pk_pk} arcsec'
#         else:
#             results_text = f'Accuracy: {self.pk_pk} arcsec<br>Repeat: {self.rep} arcsec'
#                 
#         fig.add_trace(go.Table(
#             header=dict(values=["Results"], align='left'),
#             cells=dict(values=[results_text.split('<br>')], align='left')), row=2, col=1)
# 
#         # Comments Text Box
#         comments_text = f'System Serial Number: {self.sys_serial}-{self.axis}<br>Stage Serial Number: {self.st_serial}<br>Stage: {self.stage_type}<br>Date: {self.current_date} {self.current_time}<br>Operator: {self.oper}<br>Comments: {self.comments}'
#         fig.add_trace(go.Table(
#             header=dict(values=["Comments"], align='left'),
#             cells=dict(values=[comments_text.split('<br>')], align='left')), row=2, col=2)
# 
#         # Test Conditions Text Box
#         degree_sign = u'\N{DEGREE SIGN}'
#         test_conditions_text = f'Temperature: {self.temp} {degree_sign}C<br>Step Size: {round(self.step_size, 6)} {self.units}<br>Travel: {round(self.travel, 6)} {self.units}<br>Start Position: {self.start_pos} {self.units}'
#         
#         fig.add_trace(go.Table(
#             header=dict(values=["Test Conditions"], align='left'),
#             cells=dict(values=[test_conditions_text.split('<br>')], align='left')), row=2, col=3)
# =============================================================================

        fig.update_layout(template='plotly_white',title_text="Aerotech PDF Report")

        html_output_file = f'{self.sys_serial}-{self.axis}_Verification.html' if self.is_cal else f'{self.sys_serial}-{self.axis}_Accuracy.html'
        html_file_path = os.path.join(self.folder_path, 'Customer Files', 'Plots')
        #save_file = os.path.join(pdf_file_path, output_file)
        
        # Save Plotly plot as HTML
        plotly_html_file = os.path.join(html_file_path, html_output_file)
        fig.write_html(plotly_html_file)
        
        import webbrowser
        webbrowser.open(plotly_html_file)
        
        #fig.write_image(save_file)
        fig.show() 
        
    def angular_pdf(self):
        self.start_path = ('O:/')
        self.sys_serial = str(self.sys_serial)
        self.folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(self.start_path) for dir_name in dirs if str(self.sys_serial[0:6]) in dir_name), None)

        # This cell of the script will be used to generate a pdf in the AerotechFooter Format
        #global fig
        for attr in ['pk_pk_X', 'pk_pk_Y']:
            setattr(self, attr, float(getattr(self, attr)))


        #Center data about zero for plotting
        mean_forward_X = np.mean(self.forward_X)
        mean_forward_Y = np.mean(self.forward_Y)
        
        forward_X = self.forward_X - mean_forward_X
        forward_Y = self.forward_Y - mean_forward_Y
        
        if self.test_type == 'Bidirectional':
            reverse_X = self.reverse_X - mean_forward_X
            reverse_Y = self.reverse_Y - mean_forward_Y
            for attr in ['rep_X', 'rep_Y']:
                setattr(self, attr, float(getattr(self, attr)))
    
        
        title_font = fm.FontProperties(family='Times New Roman', size=12, weight='bold')
        label_font = fm.FontProperties(family='Times New Roman', size=10, style='italic')
        #plt.rcParams.update({'font.size': 10})
        fig, ax1, ax2, ax3, ax4 = AerotechFormat.makeTemplate()
        
        ax1 = plt.subplot2grid((19, 3),(3,0), rowspan = 8, colspan = 3,)
        plt.title('Angular Errors', fontproperties=title_font)
    
        #Accuracy plot
        plt.ylabel('Accuracy (arcsec)',fontproperties=label_font)
        plt.xlabel('Position ({})'.format(self.units),fontproperties=label_font)
        if self.test_type == "Bidirectional":
            ax1.plot(self.for_pos_fbk, forward_X, '-b', label='Forward', marker='o')
            ax1.plot(self.for_pos_fbk, reverse_X, '-r', label='Reverse', marker='x')
            plt.legend(loc='upper right')
        else:
            ax1.plot(self.for_pos_fbk, forward_X, '-b', label='Accuracy', marker='o')
            plt.legend(loc='upper right')
    
        #Results Text Box
        if self.test_type != "Bidirectional":
            ax2.text(0.02,.8, 'Accuracy: {} arcsec'.format(round(self.pk_pk_X,3)), color = 'black', size = 8.5)
        else:
            ax2.text(0.02,.8, 'Accuracy: {} arcsec'.format(round(self.pk_pk_X,3)), color = 'black', size = 8.5)
            ax2.text(0.02,.725, 'Repeat: {} arcsec'.format(round(self.rep_X,3)), color = 'black', size = 8.5)    
        
        #Comments Text Box
        ax3.text(0.02, .8, 'System Serial Number: {}'.format(str(self.sys_serial) + '-' + str(self.axis)), color = 'black', size = 9)
        ax3.text(0.02, .725, 'Stage Serial Number: {}'.format(self.st_serial), color = 'black', size = 9)
        ax3.text(0.02, .65, 'Stage: {}'.format(self.stage_type),color='black',size=9)
        ax3.text(0.02, .575, 'Date: {} {}'.format(self.current_date,self.current_time), color = 'black', size= 9)
        ax3.text(0.02, .500, 'Operator: {}'.format(self.oper), color = 'black', size= 9)
        ax3.text(0.02, .275, 'Comments: {}'.format(self.comments), color = 'black', size = 10, verticalalignment = 'top')

        #Test Conditions Text Box
        degree_sign = u'\N{DEGREE SIGN}'
        ax4.text(.02, .8, 'Temperature: {} {}C'.format(self.temp, degree_sign), color = 'black', size = 9)
        ax4.text(.02, .725, 'Step Size: {} {}'.format(round(self.step_size,6),self.units), color = 'black', size = 9)
        ax4.text(.02, .65, 'Travel: {} {}'.format(round(self.travel,6), self.units), color = 'black', size = 9)
        ax4.text(.02, .575, 'Start Position: {} {}'.format(self.start_pos, self.units), color = 'black', size = 9)


        
        output_file = str(self.sys_serial + '-' + self.axis + "_Angular.pdf")
                
        pdf_file_path = self.folder_path + '/Customer Files/Plots'
        save_file = pdf_file_path + '/' + output_file
        fig.get_figure().savefig(save_file)
        
        self.angular_plotly()
        
    def angular_plotly(self):
        self.start_path = ('O:/')
        self.sys_serial = str(self.sys_serial)
        self.folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(self.start_path) for dir_name in dirs if str(self.sys_serial[0:6]) in dir_name), None)
        
        
        # This cell of the script will be used to generate a pdf in the AerotechFooter Format
        #global fig
        for attr in ['pk_pk_X', 'pk_pk_Y']:
            setattr(self, attr, float(getattr(self, attr)))


        #Center data about zero for plotting
        mean_forward_X = np.mean(self.forward_X)
        mean_forward_Y = np.mean(self.forward_Y)
        
        forward_X = self.forward_X - mean_forward_X
        forward_Y = self.forward_Y - mean_forward_Y
        
        if self.test_type == 'Bidirectional':
            reverse_X = self.reverse_X - mean_forward_X
            reverse_Y = self.reverse_Y - mean_forward_Y
            for attr in ['rep_X', 'rep_Y']:
                setattr(self, attr, float(getattr(self, attr)))
        
        # Create the figure with subplots
        fig = make_subplots(
            rows=2, cols=3,
            row_heights=[1.5, 0.5],
            vertical_spacing=0.1,
            specs=[[{"type": "scatter", "colspan": 3}, None, None],
                   [{"type": "table"}, {"type": "table"}, {"type": "table"}]]
        )
        
        # Add image
        fig.add_layout_image(
            dict(
                source="AerotechLogo.png",
                xref="paper", yref="paper",
                x=0.2, y=0.4,
                sizex=0.2, sizey=0.2,
                xanchor="center", yanchor="top"
            )
        )

        # Accuracy plot
        accuracy_trace = go.Scatter(x=self.for_pos_fbk, y=forward_X, mode='lines+markers', name='Forward', marker=dict(color='blue'))
        fig.add_trace(accuracy_trace, row=1, col=1)

        if self.test_type == "Bidirectional":
            reverse_trace = go.Scatter(x=self.for_pos_fbk, y=reverse_X, mode='lines+markers', name='Reverse', marker=dict(color='red'))
            fig.add_trace(reverse_trace, row=1, col=1)

        fig.update_xaxes(title_text=f"Position ({self.units})", showline=True, linewidth=2, linecolor='black', ticks="outside", showgrid=False, zeroline=False, row=1, col=1)
        fig.update_yaxes(title_text="Accuracy (arcsec)", showline=True, linewidth=2, linecolor='black', ticks="outside", showgrid=False, zeroline=False, row=1, col=1)
        
        # Results Text Box
        results_text = ""
        if self.test_type != "Bidirectional":
            results_text = f'Accuracy: {self.pk_pk_X} arcsec'
        else:
            results_text = f'Accuracy: {self.pk_pk_X} arcsec<br>Repeat: {self.rep_X} arcsec'
                
        fig.add_trace(go.Table(
            header=dict(values=["Results"], align='left'),
            cells=dict(values=[results_text.split('<br>')], align='left')), row=2, col=1)

        # Comments Text Box
        comments_text = f'System Serial Number: {self.sys_serial}-{self.axis}<br>Stage Serial Number: {self.st_serial}<br>Stage: {self.stage_type}<br>Date: {self.current_date} {self.current_time}<br>Operator: {self.oper}<br>Comments: {self.comments}'
        fig.add_trace(go.Table(
            header=dict(values=["Comments"], align='left'),
            cells=dict(values=[comments_text.split('<br>')], align='left')), row=2, col=2)

        # Test Conditions Text Box
        degree_sign = u'\N{DEGREE SIGN}'
        test_conditions_text = f'Temperature: {self.temp} {degree_sign}C<br>Step Size: {round(self.step_size, 6)} {self.units}<br>Travel: {round(self.travel, 6)} {self.units}<br>Start Position: {self.start_pos} {self.units}'
        
        fig.add_trace(go.Table(
            header=dict(values=["Test Conditions"], align='left'),
            cells=dict(values=[test_conditions_text.split('<br>')], align='left')), row=2, col=3)

        fig.update_layout(template='plotly_white',title_text="Aerotech PDF Report")

        html_output_file = f"{self.sys_serial}-{self.axis}_Angular.html"
        html_file_path = os.path.join(self.folder_path, 'Customer Files', 'Plots')
        #save_file = os.path.join(pdf_file_path, output_file)
        
        # Save Plotly plot as HTML
        plotly_html_file = os.path.join(html_file_path, html_output_file)
        fig.write_html(plotly_html_file)
        
        import webbrowser
        webbrowser.open(plotly_html_file)
        
        #fig.write_image(save_file)
        fig.show()