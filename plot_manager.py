import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.style as style
import numpy as np

class PlotManager:
    def __init__(self, window, frame, plot_type='rotary'):
        """Initialize plot manager with window and frame"""
        self.window = window
        self.frame = frame
        self.plot_type = plot_type  # 'rotary' or 'angular'
        
        # Configure plot frame grid
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Color settings
        self.colors = {
            'background': '#FFFFFF',  # White background
            'text': '#2D2D2D',
            'grid': '#E1E1E1',
            'forward': '#1E88E5',  # Blue for forward data
            'reverse': '#E53935',   # Red for reverse data
        }
        
        # Font settings
        self.fonts = {
            'title': {'family': 'Segoe UI', 'size': 14, 'weight': 'bold'},
            'label': {'family': 'Segoe UI', 'size': 12},
            'tick': {'family': 'Segoe UI', 'size': 10}
        }
        
        # Initialize plot elements
        self.fig = None
        self.ax = None
        self.ax1 = None
        self.ax2 = None
        self.canvas = None
        self.forward_line = None
        self.reverse_line = None
        self.reverse_points = []  # Store reverse direction points
        
    def setup_plot(self, axis_name, col_axis_X=None, col_axis_Y=None):
        """Set up the plot(s) based on test type"""
        # Reset to default style
        plt.style.use('default')
        
        # Get frame dimensions
        width = self.frame.winfo_width()
        height = self.frame.winfo_height()
        dpi = self.window.winfo_fpixels('1i')
        
        # Create figure with proper dimensions
        self.fig, self.ax = plt.subplots(figsize=(width/dpi, height/dpi), dpi=dpi, facecolor=self.colors['background'])
        
        if self.plot_type == 'rotary':
            self.ax.set_title(f'{axis_name} Axis Calibration')
            self.ax.set_xlabel('Position (deg)')
            self.ax.set_ylabel('Error (arcsec)')
            
            # Initialize lines for forward and reverse data
            self.forward_line, = self.ax.plot([], [], 
                color=self.colors['forward'],
                linewidth=2,
                marker='o',
                markersize=6,
                label='Forward'
            )
            
            self.reverse_line, = self.ax.plot([], [], 
                color=self.colors['reverse'],
                linewidth=2,
                marker='x',
                markersize=6,
                label='Reverse'
            )
            
            self.ax.legend(loc='upper right',
                frameon=True,
                fancybox=True,
                shadow=True,
                prop={'family': 'Segoe UI', 'size': 10}
            )
            
        else:  # Angular testing
            self.ax.set_title(f'{axis_name} Axis Angular Error')
            self.ax.set_xlabel(f'{col_axis_X} Error (arcsec)')
            self.ax.set_ylabel(f'{col_axis_Y} Error (arcsec)')
            
            # Initialize lines for both plots
            self.forward_line1, = self.ax.plot([], [], 
                color=self.colors['forward'],
                linewidth=2,
                marker='o',
                markersize=6,
                label='Forward'
            )
            
            self.reverse_line1, = self.ax.plot([], [], 
                color=self.colors['reverse'],
                linewidth=2,
                marker='x',
                markersize=6,
                label='Reverse'
            )
            
            self.forward_line2, = self.ax.plot([], [], 
                color=self.colors['forward'],
                linewidth=2,
                marker='o',
                markersize=6,
                label='Forward'
            )
            
            self.reverse_line2, = self.ax.plot([], [], 
                color=self.colors['reverse'],
                linewidth=2,
                marker='x',
                markersize=6,
                label='Reverse'
            )
            
            self.ax.legend(loc='upper right',
                frameon=True,
                fancybox=True,
                shadow=True,
                prop={'family': 'Segoe UI', 'size': 10}
            )
        
        # Create canvas and make it fill the frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
        
        # Adjust layout
        if self.plot_type == 'rotary':
            self.fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)
        else:
            self.fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1, hspace=0.3)
            
    def _configure_axis(self, ax):
        """Configure common axis properties"""
        ax.set_facecolor(self.colors['background'])
        ax.grid(True, linestyle='--', alpha=0.7, color=self.colors['grid'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(self.colors['grid'])
        ax.spines['bottom'].set_color(self.colors['grid'])
        ax.tick_params(colors=self.colors['text'])
        ax.set_xlabel('Position', fontdict=self.fonts['label'], color=self.colors['text'])
        ax.set_ylabel('Measurement', fontdict=self.fonts['label'], color=self.colors['text'])
            
    def update_plot(self, positions, forward_data, reverse_data=None, axis_num=None):
        """Update plot(s) with new data"""
        if not self.ax:
            return
            
        if self.plot_type == 'rotary':
            # Update forward data
            self.forward_line.set_data(positions, forward_data)
            
            # Handle reverse data
            if reverse_data:
                if isinstance(reverse_data, list) and len(reverse_data) == 1:
                    # Single point update for reverse direction
                    pos, val = reverse_data[0]
                    self.reverse_points.append((pos, val))
                    
                    # Update reverse line with all collected points
                    if self.reverse_points:
                        rev_positions, rev_values = zip(*self.reverse_points)
                        self.reverse_line.set_data(rev_positions, rev_values)
            
            self.ax.set_xlabel('Position (deg)')
            self.ax.set_ylabel('Error (arcsec)')
            self.ax.grid(True, linestyle='--', alpha=0.7, color=self.colors['grid'])
            
        else:  # Angular testing
            if axis_num == 1:
                self.forward_line1.set_data(positions, forward_data)
            elif axis_num == 2:
                self.forward_line2.set_data(positions, forward_data)
            
            self.ax.set_xlabel('Error (arcsec)')
            self.ax.set_ylabel('Error (arcsec)')
            self.ax.grid(True, linestyle='--', alpha=0.7, color=self.colors['grid'])
        
        # Adjust plot limits
        self.ax.relim()
        self.ax.autoscale_view()
        
        # Redraw canvas
        self.canvas.draw_idle()
        
    def stop(self):
        """Clean up plot resources"""
        if self.fig:
            plt.close(self.fig)
            self.fig = None
            self.ax = None
            self.ax1 = None
            self.ax2 = None
            self.forward_line = None
            self.reverse_line = None
            
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
            
        # Reset to default style
        plt.style.use('default') 