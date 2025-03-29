import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from bleak import BleakScanner, BleakClient
import time
import threading
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SprintTimer")

class SprintTimerApp:
    def __init__(self, root):
        logger.info("Initializing Sprint Timer Application")
        self.root = root
        self.root.title("Sprint Timer")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Style configuration
        logger.debug("Configuring UI styles")
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f8f9fa")
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("TLabel", background="#f8f9fa", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        self.style.configure("TimerDisplay.TLabel", font=("Courier New", 48), anchor="center")
        self.style.configure("SpeedDisplay.TLabel", font=("Courier New", 48), anchor="center")
        
        # Variables
        self.start_gate = None
        self.end_gate = None
        self.start_time = 0
        self.is_timing = False
        self.timer_running = False
        self.timer_thread = None
        self.selected_distance = tk.StringVar(value="20")
        self.custom_distance = tk.StringVar()
        self.devices = {}
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill="both", expand=True)
        
        # Create the UI components
        self.create_connection_frame()
        self.create_timer_frame()
        
        # Add console output frame
        self.create_console_frame()
        
        # Start the async event loop
        self.loop = asyncio.new_event_loop()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Add initial console message
        self.append_to_console("Application started")
        self.append_to_console(f"Python version: {sys.version}")
        self.append_to_console("Click 'Scan for Devices' to begin")
        
        logger.info("Application UI initialized and ready")
    
    def create_connection_frame(self):
        logger.debug("Creating connection frame")
        # Connection frame
        connection_frame = ttk.LabelFrame(self.main_frame, text="Gate Connection", padding=10)
        connection_frame.pack(fill="x", pady=10)
        
        # Device selection frame
        device_frame = ttk.Frame(connection_frame)
        device_frame.pack(fill="x", pady=5)
        
        # Start gate selection
        start_gate_frame = ttk.Frame(device_frame)
        start_gate_frame.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        ttk.Label(start_gate_frame, text="Start Gate").pack(side="top", anchor="w")
        self.start_gate_var = tk.StringVar()
        self.start_gate_combo = ttk.Combobox(start_gate_frame, textvariable=self.start_gate_var, state="readonly")
        self.start_gate_combo.pack(side="top", fill="x", pady=5)
        
        # End gate selection
        end_gate_frame = ttk.Frame(device_frame)
        end_gate_frame.pack(side="right", expand=True, fill="x", padx=(5, 0))
        
        ttk.Label(end_gate_frame, text="End Gate").pack(side="top", anchor="w")
        self.end_gate_var = tk.StringVar()
        self.end_gate_combo = ttk.Combobox(end_gate_frame, textvariable=self.end_gate_var, state="readonly")
        self.end_gate_combo.pack(side="top", fill="x", pady=5)
        
        # Button frame
        button_frame = ttk.Frame(connection_frame)
        button_frame.pack(fill="x", pady=10)
        
        # Scan button
        scan_button = ttk.Button(button_frame, text="Scan for Devices", command=self.scan_for_devices)
        scan_button.pack(side="left", padx=5)
        
        # Connect buttons
        connect_start_button = ttk.Button(button_frame, text="Connect Start Gate", command=lambda: self.connect_gate("start"))
        connect_start_button.pack(side="left", padx=5)
        
        connect_end_button = ttk.Button(button_frame, text="Connect End Gate", command=lambda: self.connect_gate("end"))
        connect_end_button.pack(side="left", padx=5)
        
        # Status frame
        status_frame = ttk.Frame(connection_frame)
        status_frame.pack(fill="x", pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side="left")
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side="left", padx=5)
    
    def create_timer_frame(self):
        logger.debug("Creating timer frame")
        # Timer frame
        timer_frame = ttk.LabelFrame(self.main_frame, text="Sprint Timer", padding=10)
        timer_frame.pack(fill="x", pady=10)
        
        # Results display frame
        results_frame = ttk.Frame(timer_frame)
        results_frame.pack(fill="x", pady=10)
        
        # Time display (left)
        time_frame = ttk.Frame(results_frame)
        time_frame.pack(side="left", expand=True, fill="both", padx=(0, 5))
        
        ttk.Label(time_frame, text="Time (seconds)", font=("Segoe UI", 12, "bold")).pack(anchor="center", pady=5)
        self.time_display = ttk.Label(time_frame, text="00.000", style="TimerDisplay.TLabel", background="#f5f5f5", 
                                     width=10, anchor="center", relief="sunken")
        self.time_display.pack(fill="both", expand=True, pady=5)
        
        # Speed display (right)
        speed_frame = ttk.Frame(results_frame)
        speed_frame.pack(side="right", expand=True, fill="both", padx=(5, 0))
        
        ttk.Label(speed_frame, text="Speed (km/h)", font=("Segoe UI", 12, "bold")).pack(anchor="center", pady=5)
        self.speed_display = ttk.Label(speed_frame, text="0.0", style="SpeedDisplay.TLabel", background="#f5f5f5", 
                                      width=10, anchor="center", relief="sunken")
        self.speed_display.pack(fill="both", expand=True, pady=5)
        
        # Controls frame
        controls_frame = ttk.Frame(timer_frame)
        controls_frame.pack(fill="x", pady=10)
        
        # Reset button
        reset_button = ttk.Button(controls_frame, text="Reset Timer", command=self.reset_timer)
        reset_button.pack(side="left", padx=5)
        
        # Distance selector
        ttk.Label(controls_frame, text="Distance:").pack(side="left", padx=(20, 5))
        distance_combo = ttk.Combobox(controls_frame, textvariable=self.selected_distance, 
                                     values=["20", "40", "custom"], width=8, state="readonly")
        distance_combo.pack(side="left", padx=5)
        distance_combo.bind("<<ComboboxSelected>>", self.on_distance_change)
        
        # Custom distance entry
        self.custom_distance_entry = ttk.Entry(controls_frame, textvariable=self.custom_distance, width=8)
        self.custom_distance_entry.pack(side="left", padx=5)
        self.custom_distance_entry.configure(state="disabled")
        
        ttk.Label(controls_frame, text="meters").pack(side="left")
        
        # Manual test buttons (for development)
        test_frame = ttk.Frame(timer_frame)
        test_frame.pack(fill="x", pady=10)
        
        test_start_button = ttk.Button(test_frame, text="Test Start Gate", command=self.test_start_gate)
        test_start_button.pack(side="left", padx=5)
        
        test_end_button = ttk.Button(test_frame, text="Test End Gate", command=self.test_end_gate)
        test_end_button.pack(side="left", padx=5)
    
    def create_console_frame(self):
        logger.debug("Creating console output frame")
        # Console frame for log output
        console_frame = ttk.LabelFrame(self.main_frame, text="Console Output", padding=10)
        console_frame.pack(fill="both", expand=True, pady=10)
        
        # Create text widget with scrollbar
        self.console_text = tk.Text(console_frame, height=6, width=70, wrap="word")
        self.console_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(console_frame, orient="vertical", command=self.console_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.console_text.configure(yscrollcommand=scrollbar.set)
        
        # Configure text widget
        self.console_text.configure(state="disabled", background="#f0f0f0", foreground="#333333")
    
    def append_to_console(self, message):
        """Add a message to the console output"""
        self.console_text.configure(state="normal")
        self.console_text.insert(tk.END, f"{message}\n")
        self.console_text.see(tk.END)  # Scroll to the end
        self.console_text.configure(state="disabled")
        logger.info(message)  # Also log to the console
    
    def on_distance_change(self, event):
        """Handle distance selection change"""
        if self.selected_distance.get() == "custom":
            self.custom_distance_entry.configure(state="normal")
            self.append_to_console("Selected custom distance")
        else:
            self.custom_distance_entry.configure(state="disabled")
            self.append_to_console(f"Selected {self.selected_distance.get()} meter distance")
    
    def update_status(self, message):
        """Update the status label"""
        self.status_label.config(text=message)
        self.append_to_console(f"Status: {message}")
        
    def scan_for_devices(self):
        """Scan for Bluetooth devices"""
        self.update_status("Scanning for devices...")
        self.append_to_console("Starting Bluetooth scan...")
        threading.Thread(target=self._scan_for_devices_thread, daemon=True).start()
    
    def _scan_for_devices_thread(self):
        """Thread function to scan for devices"""
        self.append_to_console("Scanning thread started")
        
        async def scan():
            try:
                self.append_to_console("Looking for Bluetooth devices...")
                devices = await BleakScanner.discover()
                self.append_to_console(f"Scan completed, found {len(devices)} devices")
                
                device_dict = {}
                for d in devices:
                    name = d.name or 'Unknown'
                    address = d.address
                    self.append_to_console(f"Found device: {name} ({address})")
                    device_dict[f"{name} ({address})"] = d
                
                return device_dict
            except Exception as e:
                self.append_to_console(f"Error during scan: {str(e)}")
                raise
        
        try:
            device_dict = asyncio.run(scan())
            
            # Update the UI from the main thread
            self.root.after(0, lambda: self._update_device_lists(device_dict))
        except Exception as e:
            error_msg = f"Error scanning: {str(e)}"
            self.root.after(0, lambda: self.update_status(error_msg))
            self.append_to_console(f"EXCEPTION: {error_msg}")
    
    def _update_device_lists(self, device_dict):
        """Update the device dropdown lists with scan results"""
        if not device_dict:
            self.update_status("No devices found!")
            return
        
        self.devices = device_dict
        device_names = list(device_dict.keys())
        
        self.start_gate_combo['values'] = device_names
        self.end_gate_combo['values'] = device_names
        
        if device_names:
            self.start_gate_combo.current(0)
            self.end_gate_combo.current(0)
            self.append_to_console(f"Updated device lists with {len(device_names)} devices")
        
        self.update_status(f"Found {len(device_names)} devices")
    
    def connect_gate(self, gate_type):
        """Connect to a selected gate"""
        if gate_type == "start":
            selected = self.start_gate_var.get()
        else:
            selected = self.end_gate_var.get()
        
        if not selected:
            error_msg = "No device selected!"
            messagebox.showerror("Error", error_msg)
            self.append_to_console(error_msg)
            return
        
        status_msg = f"Connecting to {selected}..."
        self.update_status(status_msg)
        device = self.devices.get(selected)
        
        if not device:
            error_msg = f"Device {selected} not found in device list"
            self.append_to_console(error_msg)
            self.update_status("Error: Device not found")
            return
        
        self.append_to_console(f"Starting connection thread for {gate_type} gate")
        threading.Thread(target=self._connect_gate_thread, 
                        args=(gate_type, device), 
                        daemon=True).start()
    
    def _connect_gate_thread(self, gate_type, device):
        """Thread function to connect to a gate"""
        self.append_to_console(f"Connection thread started for {gate_type} gate: {device.address}")
        
        async def connect():
            try:
                self.append_to_console(f"Creating BleakClient for {device.address}")
                client = BleakClient(device.address)
                
                self.append_to_console(f"Attempting to connect to {device.address}")
                await client.connect()
                
                if not client.is_connected:
                    self.append_to_console("Connection failed: device reported not connected")
                    raise Exception("Failed to connect")
                
                self.append_to_console(f"Connected to {device.address}")
                
                # Discover services
                self.append_to_console("Discovering services and characteristics...")
                services = {}
                for service in client.services:
                    self.append_to_console(f"Service found: {service.uuid}")
                    characteristics = []
                    for char in service.characteristics:
                        char_info = f"{char.uuid}: {char.description}"
                        characteristics.append(char_info)
                        self.append_to_console(f"  Characteristic: {char_info}")
                    services[service.uuid] = characteristics
                
                # Subscribe to notifications - this is where you'll need to adjust for your specific gates
                # For now, we're just storing the client for manual testing
                
                return client, services
            except Exception as e:
                self.append_to_console(f"Connection error: {str(e)}")
                raise Exception(f"Connection error: {str(e)}")
        
        try:
            client, services = asyncio.run(connect())
            
            # Update the UI from the main thread
            if gate_type == "start":
                self.start_gate = client
                status = f"Start gate connected"
            else:
                self.end_gate = client
                status = f"End gate connected"
            
            self.root.after(0, lambda: self.update_status(status))
            
            # Print discovered services for debugging
            self.append_to_console(f"Services for {gate_type} gate:")
            for service_uuid, characteristics in services.items():
                self.append_to_console(f"  Service: {service_uuid}")
                for char in characteristics:
                    self.append_to_console(f"    Characteristic: {char}")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda: self.update_status(error_msg))
            self.append_to_console(f"EXCEPTION in connection thread: {error_msg}")
    
    def test_start_gate(self):
        """Simulate a start gate trigger for testing"""
        self.append_to_console("Test start gate triggered")
        self.start_time = time.time()
        self.is_timing = True
        self.start_timer_updates()
        self.update_status("Timer started")
    
    def test_end_gate(self):
        """Simulate an end gate trigger for testing"""
        if not self.is_timing:
            self.update_status("Start the timer first")
            self.append_to_console("End gate test failed - timer not running")
            return
        
        self.append_to_console("Test end gate triggered")
        self.end_time = time.time()
        elapsed_time = self.end_time - self.start_time
        self.is_timing = False
        
        # Stop the timer updates
        self.timer_running = False
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1.0)
        
        # Update the display with final time
        self.time_display.config(text=f"{elapsed_time:.3f}")
        
        # Calculate speed
        try:
            if self.selected_distance.get() == "custom":
                distance = float(self.custom_distance.get())
            else:
                distance = float(self.selected_distance.get())
            
            speed_mps = distance / elapsed_time
            speed_kmh = speed_mps * 3.6  # Convert m/s to km/h
            self.speed_display.config(text=f"{speed_kmh:.1f}")
            
            result_msg = f"Sprint completed: {elapsed_time:.3f}s, {speed_kmh:.1f} km/h"
            self.update_status(result_msg)
            self.append_to_console(result_msg)
        except ValueError:
            error_msg = "Invalid distance value"
            self.update_status(error_msg)
            self.append_to_console(error_msg)
    
    def start_timer_updates(self):
        """Start the timer update thread"""
        def update_timer():
            self.append_to_console("Timer update thread started")
            self.timer_running = True
            while self.timer_running:
                if self.is_timing:
                    elapsed = time.time() - self.start_time
                    self.root.after(0, lambda t=elapsed: self.time_display.config(text=f"{t:.3f}"))
                time.sleep(0.01)  # Update every 10ms
            self.append_to_console("Timer update thread stopped")
        
        self.timer_thread = threading.Thread(target=update_timer, daemon=True)
        self.timer_thread.start()
    
    def reset_timer(self):
        """Reset the timer display"""
        self.append_to_console("Resetting timer")
        self.is_timing = False
        self.timer_running = False
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1.0)
        
        self.time_display.config(text="00.000")
        self.speed_display.config(text="0.0")
        self.update_status("Timer reset")
    
    def on_closing(self):
        """Clean up when the application is closed"""
        self.append_to_console("Application closing, cleaning up...")
        # Stop the timer thread
        self.timer_running = False
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1.0)
        
        # Disconnect BLE clients
        async def disconnect():
            if self.start_gate and self.start_gate.is_connected:
                self.append_to_console("Disconnecting start gate")
                await self.start_gate.disconnect()
            if self.end_gate and self.end_gate.is_connected:
                self.append_to_console("Disconnecting end gate")
                await self.end_gate.disconnect()
        
        if self.start_gate or self.end_gate:
            try:
                self.append_to_console("Running disconnect routines")
                asyncio.run(disconnect())
            except Exception as e:
                self.append_to_console(f"Error during disconnect: {str(e)}")
        
        self.append_to_console("Goodbye!")
        logger.info("Application closing")
        self.root.destroy()

if __name__ == "__main__":
    logger.info("Starting Sprint Timer Application")
    
    try:
        # Create the Tkinter root window
        root = tk.Tk()
        
        # Create the application
        app = SprintTimerApp(root)
        
        # Start the Tkinter event loop
        logger.info("Entering Tkinter main loop")
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        if 'root' in locals() and root:
            messagebox.showerror("Critical Error", f"An unhandled error occurred: {str(e)}")