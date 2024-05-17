import tkinter as tk
from tkinter import ttk
import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time

class OscilloscopeApp(tk.Tk):
    def __init__(self, port, baudrate=115200):
        super().__init__()
        self.title("Arduino Oscilloscope")
        
        # Serial connection
        self.ser = serial.Serial(port, baudrate)
        
        # Oscilloscope data
        self.data_length = 1000  # Points to display
        self.channel1 = np.zeros(self.data_length)
        self.channel2 = np.zeros(self.data_length)
        
        # Flags for data handling
        self.is_paused = False
        self.data_ready = False
        
        # Setup GUI
        self.create_widgets()
        
        # Start data receiving in a separate thread
        self.thread = threading.Thread(target=self.receive_data)
        self.thread.start()
    
    def create_widgets(self):
        # Setup matplotlib figure for plotting
        self.figure, self.ax = plt.subplots(1, 1)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        control_frame = tk.Frame(self)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.update_button = ttk.Button(control_frame, text="Update", command=self.update_plot)
        self.update_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_button.config(text="Play" if self.is_paused else "Pause")
    
    def receive_data(self):
        # Continuously receive data from Arduino
        while True:
            if not self.is_paused:
                try:
                    line = self.ser.readline().decode().strip()
                    values = list(map(int, line.split(',')))
                    if len(values) == 2:
                        self.channel1 = np.roll(self.channel1, -1)
                        self.channel2 = np.roll(self.channel2, -1)
                        self.channel1[-1] = values[0]
                        self.channel2[-1] = values[1]
                        self.data_ready = True
                except Exception as e:
                    print("Error reading serial:", e)
            time.sleep(0.01)
    
    def update_plot(self):
        if self.data_ready:
            self.ax.clear()
            self.ax.plot(self.channel1, label="Channel 1")
            self.ax.plot(self.channel2, label="Channel 2")
            self.ax.legend()
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Value")
            self.ax.set_title("Arduino Oscilloscope")
            self.canvas.draw()
            self.data_ready = False

# Example usage:
# You need to replace '/dev/ttyUSB0' with your Arduino's serial port.
# In Windows, it might be 'COM3', 'COM4', etc.
if __name__ == "__main__":
    app = OscilloscopeApp(port='COM6')
    app.mainloop()
