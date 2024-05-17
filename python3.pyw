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
        self.ser = serial.Serial(port, baudrate)
        self.data_length = 1000
        self.channel1 = np.zeros(self.data_length)
        self.triggered = False
        self.last_value = 0
        self.is_paused = False
        self.trigger_type = 'none'
        self.trigger_level = 512
        self.points_per_second = 0
        self.create_widgets()
        self.start_receiving_data()
        self.start_auto_update()

    def create_widgets(self):
        self.figure, self.ax = plt.subplots(1, 1)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        control_frame = tk.Frame(self)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.trigger_combobox = ttk.Combobox(
            control_frame,
            values=["none", "rising", "falling"],
            state="readonly",
            textvariable=tk.StringVar(value=self.trigger_type),
        )
        self.trigger_combobox.bind("<<ComboboxSelected>>", self.on_trigger_change)
        self.trigger_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        self.points_per_second_label = ttk.Label(control_frame, text="Points/sec: 0")
        self.points_per_second_label.pack(side=tk.RIGHT, padx=5, pady=5)

    def on_trigger_change(self, event):
        self.trigger_type = self.trigger_combobox.get()
        self.triggered = False

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_button.config(text="Play" if self.is_paused else "Pause")

    def start_receiving_data(self):
        self.data_thread = threading.Thread(target=self.receive_data, daemon=True)
        self.data_thread.start()

    def receive_data(self):
        count = 0
        start_time = time.time()
        while True:
            if not self.is_paused:
                try:
                    line = self.ser.readline().decode().strip()
                    value = int(line)
                    if self.trigger_type == "none":
                        self.triggered = True
                    elif not self.triggered:
                        if (
                            self.trigger_type == "rising" 
                            and value > self.trigger_level 
                            and self.last_value <= self.trigger_level
                        ) or (
                            self.trigger_type == "falling" 
                            and value < self.trigger_level 
                            and self.last_value >= self.trigger_level
                        ):
                            self.triggered = True
                    if self.triggered:
                        self.channel1 = np.roll(self.channel1, -1)
                        self.channel1[-1] = value
                    self.last_value = value
                    count += 1
                except Exception:
                    pass
            if time.time() - start_time >= 1:
                self.points_per_second = count
                self.points_per_second_label.config(text=f"Points/sec: {count}")
                count = 0
                start_time = time.time()
            time.sleep(0.001)

    def start_auto_update(self):
        self.update_plot()
        self.after(50, self.start_auto_update)

    def update_plot(self):
        if not self.is_paused:
            self.ax.clear()
            self.ax.plot(self.channel1, label="Channel 1")
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Amplitude")
            self.ax.set_title("Arduino Oscilloscope")
            self.ax.set_ylim(0, 1024)
            self.ax.legend()
            self.canvas.draw()

if __name__ == "__main__":
    port = 'COM6'
    app = OscilloscopeApp(port=port)
    app.mainloop()
