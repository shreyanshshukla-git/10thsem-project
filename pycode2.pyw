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
        self.triggered = False
        self.last_value = 0

        # Control variables
        self.is_paused = False
        self.trigger_type = 'none'  # Default trigger type
        self.trigger_level = 512  # Middle value for trigger
        self.points_per_second = 0

        # Create widgets and start receiving data
        self.create_widgets()
        self.start_receiving_data()
        self.start_auto_update()

    def create_widgets(self):
        # Setup matplotlib figure for plotting
        self.figure, self.ax = plt.subplots(1, 1)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Control panel
        control_frame = tk.Frame(self)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Pause/play button
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Trigger type dropdown
        self.trigger_combobox = ttk.Combobox(
            control_frame,
            values=["none", "rising", "falling"],
            state="readonly",
            textvariable=tk.StringVar(value=self.trigger_type)
        )
        self.trigger_combobox.bind("<<ComboboxSelected>>", self.on_trigger_change)
        self.trigger_combobox.pack(side=tk.LEFT, padx=5, pady=5)

        # Points per second display
        self.points_per_second_label = ttk.Label(control_frame, text="Points/sec: 0")
        self.points_per_second_label.pack(side=tk.RIGHT, padx=5, pady=5)

    def on_trigger_change(self, event):
        self.trigger_type = self.trigger_combobox.get()
        self.triggered = False  # Reset the trigger state when changing type

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_button.config(text="Play" if self.is_paused else "Pause")

    def start_receiving_data(self):
        # Start a thread to receive data from Arduino
        self.data_thread = threading.Thread(target=self.receive_data, daemon=True)
        self.data_thread.start()

    def receive_data(self):
        count = 0  # To measure points per second
        start_time = time.time()

        while True:
            if not self.is_paused:
                try:
                    line = self.ser.readline().decode().strip()
                    value = int(line)  # Expecting a single integer value

                    # Check if the trigger condition is met
                    if self.trigger_type == "none":
                        self.triggered = True
                    elif not self.triggered:
                        if (self.trigger_type == "rising" and value > self.trigger_level and self.last_value <= self.trigger_level) or (
                            self.trigger_type == "falling" and value < self.trigger_level and self.last_value >= self.trigger_level):
                            self.triggered = True

                    if self.triggered:
                        # Shift data and add new value at the end
                        self.channel1 = np.roll(self.channel1, -1)
                        self.channel1[-1] = value

                    self.last_value = value
                    count += 1
                except Exception as e:
                    print("Error reading serial:", e)

            # Update points per second every second
            if time.time() - start_time >= 1:
                self.points_per_second = count
                self.points_per_second_label.config(text=f"Points/sec: {count}")
                count = 0
                start_time = time.time()

            time.sleep(0.001)

    def start_auto_update(self):
        # Schedule periodic updates to the plot
        self.update_plot()
        self.after(50, self.start_auto_update)  # Update every 50 ms

    def update_plot(self):
        if not self.is_paused:
            self.ax.clear()
            self.ax.plot(self.channel1, label="Channel 1")
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Amplitude")
            self.ax.set_title("Arduino Oscilloscope")
            self.ax.set_ylim(0, 1024)  # Default Arduino analogRead range
            self.ax.legend()
            self.canvas.draw()

# Example usage:
# Replace '/dev/ttyUSB0' with your Arduino's serial port.
# In Windows, it might be 'COM3', 'COM4', etc.
if __name__ == "__main__":
    port = 'COM6'  # Adjust to your Arduino's serial port
    app = OscilloscopeApp(port=port)
    app.mainloop()
