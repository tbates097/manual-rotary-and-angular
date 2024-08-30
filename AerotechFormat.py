# -*- coding: utf-8 -*-
"""
Created on Thu May 26 15:08:17 2022

@author: shunn
"""
import matplotlib.pyplot as plt
import matplotlib.image as image
from PIL import Image
import os
import sys

class AerotechFormat():
    
    #Inputs: Nothing
    #Outputs: fig = Complete Figure
    # ax1 = Main Plot
    # ax2 = Text Box 1
    # ax3 = Text Box 2
    # ax4 = Text Box 3
    
    
    def makeTemplate():
        plt.rcParams.update({'font.size': 6})
        ######################################################################
        # Plotting Begins
        ######################################################################
        rows = 7
        cols = 3
        
        # OVERALL PLOT SETTINGS #
        fig, (ax0, ax1, ax2) = plt.subplots(nrows=3, ncols=3) # Creating subplots
        fig.set_size_inches(11, 8.5) # Set overall plot size to 11" horizontal x 8.5" vertical, landscape
        plt.subplots_adjust(left=0.1, right=0.9, bottom=0.05, top=0.95) # Adjust margins of paper
        
        def resource_path(relative_path):
            """ Get absolute path to resource, works for dev and for PyInstaller """
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_path, relative_path)
        
        # AEROTECH LOGO HEADER #
        logo_path = resource_path('AerotechLogo.png') # Reading image into program
        logo = Image.open(logo_path)
        ax0 = plt.subplot2grid((rows, cols), (0, 1), rowspan=1, colspan=1) # Establishing subplot number
        ax0.imshow(logo) # Plotting imported image
        ax0.axis('off') # Hiding axes from image
        
        # PLOT 1 #
        ax1 = plt.subplot2grid((rows, cols), (1, 0), rowspan=4, colspan=3) # Estabilishing subplot number
        
        ax1.spines['top'].set_visible(False)
#        ax1.spines['bottom'].set_visible(False)
        ax1.spines['right'].set_visible(False)
#        ax1.spines['left'].set_visible(False)
        
        # TEXT BOX 1 #
        ax2 = plt.subplot2grid((rows, cols), (5, 0), rowspan=2, colspan=1)
        ax2.text(0.01, 0.9, 'Results', color='black', weight='bold',size=9)
        ax2.text(0.02, 0.10, 'Aerotech Inc.,', color='red', weight='bold',size=7)
        ax2.text(0.02, 0.05, 'Proprietary and Confidential', color='red', weight='bold',size=7)
        ax2.axes.get_xaxis().set_ticks([])
        ax2.axes.get_yaxis().set_ticks([])
        
        # TEXT BOX 2 #
        ax3 = plt.subplot2grid((rows, cols), (5, 1), rowspan=2, colspan=1)
        ax3.text(0.01, 0.90, 'Comments', color='black', weight='bold',size=9)
        ax3.axes.get_xaxis().set_ticks([])
        ax3.axes.get_yaxis().set_ticks([])
        
        # TEXT BOX 3 #
        ax4 = plt.subplot2grid((rows, cols), (5, 2), rowspan=2, colspan=1)
        ax4.text(0.01, 0.9, 'Test Conditions', color='black', weight='bold',size=9)
        ax4.axes.get_xaxis().set_ticks([])
        ax4.axes.get_yaxis().set_ticks([])
        
        # CONVERT PLOT TO PDF #
       # fig.subplots_adjust(wspace=0.075, hspace=0.75) # Adjusting subplot spacing
       # fig.savefig("%s" % (PDF_Title), format='pdf', dpi=1200, quality=100) # Plotting figure to file
       
       #Return all of the useful plots for data entry
        return fig, ax1, ax2, ax3, ax4


if __name__ == '__main__':
    AerotechFormat.makeTemplate()
    
    