import asyncio
import tkinter as tk
from tkinter import ttk, messagebox, font
from bleak import BleakScanner, BleakClient
import time
import threading
import logging
import sys
from datetime import datetime
import http.client
import urllib.parse
import json
import webbrowser
import ssl

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
        self.root.title("SmartSpeed Timer")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Style configuration
        logger.debug("Configuring UI styles")
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f8f9fa")
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("TLabel", background="#f8f9fa", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        self.style.configure("TimerDisplay.TLabel", font=("Courier New", 48), anchor="center")
        self.style.configure("SpeedDisplay.TLabel", font=("Courier New", 48), anchor="center")
        self.style.configure("TopSpeed.TLabel", font=("Segoe UI", 14, "bold"), foreground="#2c3e50")
        self.style.configure("SessionSpeed.TLabel", font=("Segoe UI", 14, "bold"), foreground="#e74c3c")
        
        # Variables
        self.smart_hub = None  # Connection to SmartHub
        self.notification_char = None  # Characteristic for notifications
        self.start_time = 0
        self.is_timing = False
        self.timer_running = False
        self.timer_thread = None
        self.selected_distance = tk.StringVar(value="20")
        self.custom_distance = tk.StringVar()
        self.devices = {}
        self.last_lane = 1  # Default lane
        self.auto_reset = tk.BooleanVar(value=True)  # Auto-reset feature
        self.pushover_enabled = tk.BooleanVar(value=False)  # Pushover notification feature
        
            # Pushover credentials - replace with your actual credentials
        self.pushover_user_key = "uGXr9nTXe1r9iukGSKf6gfMjHg7riA"
        self.pushover_api_token = "atjckic7tdkq9den59wa4796qedzor"
        
        # Statistics tracking
        self.session_sprints = []  # List to store all sprint results
        self.top_speed = 0.0
        self.top_speed_time = 0.0
        self.session_top_speed = 0.0
        self.session_top_speed_time = 0.0
        self.session_best_time = float('inf')
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill="both", expand=True)
        
        # Create the UI components
        self.create_connection_frame()
        self.create_timer_frame()
        self.create_stats_frame()
        
        # Add console output frame
        self.create_console_frame()
        
        # Start the async event loop
        self.loop = asyncio.new_event_loop()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Add initial console message
        self.append_to_console("SmartSpeed Timer application started")
        self.append_to_console(f"Python version: {sys.version}")
        self.append_to_console("Click 'Scan for SmartHub' to begin")
        
        logger.info("Application UI initialized and ready")
    
    def create_connection_frame(self):
        logger.debug("Creating connection frame")
        # Connection frame
        connection_frame = ttk.LabelFrame(self.main_frame, text="SmartHub Connection", padding=10)
        connection_frame.pack(fill="x", pady=10)
        
        # Device selection frame
        device_frame = ttk.Frame(connection_frame)
        device_frame.pack(fill="x", pady=5)
        
        # SmartHub selection
        hub_frame = ttk.Frame(device_frame)
        hub_frame.pack(expand=True, fill="x")
        
        ttk.Label(hub_frame, text="SmartHub Device").pack(side="top", anchor="w")
        self.hub_var = tk.StringVar()
        self.hub_combo = ttk.Combobox(hub_frame, textvariable=self.hub_var, state="readonly")
        self.hub_combo.pack(side="top", fill="x", pady=5)
        
        # Lane selection and settings frame
        settings_frame = ttk.Frame(connection_frame)
        settings_frame.pack(fill="x", pady=5)
        
        # Lane selection
        lane_frame = ttk.Frame(settings_frame)
        lane_frame.pack(side="left", fill="x", padx=(0, 10))
        
        ttk.Label(lane_frame, text="Lane/Track:").pack(side="left")
        self.lane_var = tk.StringVar(value="1")
        lane_combo = ttk.Combobox(lane_frame, textvariable=self.lane_var, 
                                 values=["1", "2", "3", "4", "5", "6", "7", "8"], 
                                 width=5, state="readonly")
        lane_combo.pack(side="left", padx=5)
        
        # Settings checkboxes frame
        checkbox_frame = ttk.Frame(settings_frame)
        checkbox_frame.pack(side="left", fill="x", padx=10)
        
        # Auto-reset checkbox
        auto_reset_check = ttk.Checkbutton(checkbox_frame, text="Auto-Reset Timer", 
                                          variable=self.auto_reset,
                                          command=self.toggle_auto_reset)
        auto_reset_check.pack(side="top", anchor="w")
        
        # Pushover notification checkbox
        pushover_check = ttk.Checkbutton(checkbox_frame, text="Send Pushover Notifications", 
                                        variable=self.pushover_enabled,
                                        command=self.toggle_pushover)
        pushover_check.pack(side="top", anchor="w")
        
        # Button frame
        button_frame = ttk.Frame(connection_frame)
        button_frame.pack(fill="x", pady=10)
        
        # Scan button
        scan_button = ttk.Button(button_frame, text="Scan for SmartHub", command=self.scan_for_devices)
        scan_button.pack(side="left", padx=5)
        
        # Connect button
        self.connect_button = ttk.Button(button_frame, text="Connect to SmartHub", command=self.connect_to_hub)
        self.connect_button.pack(side="left", padx=5)
        
        # Pushover settings button
        pushover_settings_button = ttk.Button(button_frame, text="Pushover Settings", command=self.show_pushover_settings)
        pushover_settings_button.pack(side="left", padx=5)
        
        # Status frame
        status_frame = ttk.Frame(connection_frame)
        status_frame.pack(fill="x", pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side="left")
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side="left", padx=5)
        
        # Connection status indicator
        self.connection_indicator = ttk.Label(status_frame, text="Disconnected", foreground="red")
        self.connection_indicator.pack(side="right")
    
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
        
        # Clear session button
        clear_session_button = ttk.Button(controls_frame, text="Clear Session Stats", command=self.clear_session_stats)
        clear_session_button.pack(side="left", padx=5)
        
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
    
    def create_stats_frame(self):
        logger.debug("Creating statistics frame")
        # Stats frame
        stats_frame = ttk.LabelFrame(self.main_frame, text="Performance Statistics", padding=10)
        stats_frame.pack(fill="x", pady=10)
        
        # Top stats frame
        top_stats_frame = ttk.Frame(stats_frame)
        top_stats_frame.pack(fill="x", pady=5)
        
        # All-time top speed
        all_time_frame = ttk.Frame(top_stats_frame)
        all_time_frame.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        ttk.Label(all_time_frame, text="All-Time Top Speed", font=("Segoe UI", 11)).pack(anchor="center")
        self.top_speed_display = ttk.Label(all_time_frame, text="0.0 km/h", style="TopSpeed.TLabel")
        self.top_speed_display.pack(anchor="center", pady=5)
        self.top_speed_time_display = ttk.Label(all_time_frame, text="(00.000s)")
        self.top_speed_time_display.pack(anchor="center")
        
        # Session top speed
        session_frame = ttk.Frame(top_stats_frame)
        session_frame.pack(side="right", expand=True, fill="x", padx=(5, 0))
        
        ttk.Label(session_frame, text="Session Top Speed", font=("Segoe UI", 11)).pack(anchor="center")
        self.session_speed_display = ttk.Label(session_frame, text="0.0 km/h", style="SessionSpeed.TLabel")
        self.session_speed_display.pack(anchor="center", pady=5)
        self.session_time_display = ttk.Label(session_frame, text="(00.000s)")
        self.session_time_display.pack(anchor="center")
        
        # Recent results frame
        recent_frame = ttk.LabelFrame(stats_frame, text="Recent Sprints", padding=5)
        recent_frame.pack(fill="x", pady=10)
        
        # Create a treeview for sprint history
        columns = ("time", "date", "distance", "speed")
        self.sprints_tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=5)
        
        # Define headings
        self.sprints_tree.heading("time", text="Time (s)")
        self.sprints_tree.heading("date", text="Timestamp")
        self.sprints_tree.heading("distance", text="Distance (m)")
        self.sprints_tree.heading("speed", text="Speed (km/h)")
        
        # Define columns
        self.sprints_tree.column("time", width=80, anchor="center")
        self.sprints_tree.column("date", width=150, anchor="center")
        self.sprints_tree.column("distance", width=100, anchor="center")
        self.sprints_tree.column("speed", width=100, anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(recent_frame, orient="vertical", command=self.sprints_tree.yview)
        self.sprints_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.sprints_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
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
    
    def show_pushover_settings(self):
        """Show a dialog to configure Pushover settings"""
        # Create a new top-level window
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Pushover Settings")
        settings_window.geometry("500x300")
        settings_window.transient(self.root)  # Make it float on top of the main window
        settings_window.grab_set()  # Make it modal
        
        # Create a frame for the settings
        settings_frame = ttk.Frame(settings_window, padding=20)
        settings_frame.pack(fill="both", expand=True)
        
        # Add instructions
        instructions = ttk.Label(settings_frame, 
                                text="Enter your Pushover credentials below. You can find these on your Pushover dashboard.",
                                wraplength=460)
        instructions.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))
        
        # Create input fields for Pushover credentials
        ttk.Label(settings_frame, text="User Key:").grid(row=1, column=0, sticky="w", pady=5)
        user_key_entry = ttk.Entry(settings_frame, width=40)
        user_key_entry.grid(row=1, column=1, pady=5)
        user_key_entry.insert(0, self.pushover_user_key if self.pushover_user_key != "YOUR_USER_KEY" else "")
        
        ttk.Label(settings_frame, text="API Token:").grid(row=2, column=0, sticky="w", pady=5)
        api_token_entry = ttk.Entry(settings_frame, width=40)
        api_token_entry.grid(row=2, column=1, pady=5)
        api_token_entry.insert(0, self.pushover_api_token if self.pushover_api_token != "YOUR_API_TOKEN" else "")
        
        # Status info
        status_label = ttk.Label(settings_frame, text="")
        status_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(15, 5))
        
        # Create a button frame
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Helper function to update status
        def update_status(message, is_error=False):
            status_label.config(text=message, foreground="red" if is_error else "green")
        
        # Test button
        def test_pushover():
            user_key = user_key_entry.get().strip()
            api_token = api_token_entry.get().strip()
            
            if not user_key or not api_token:
                update_status("Please enter both User Key and API Token", True)
                return
            
            # Save the entered values
            self.pushover_user_key = user_key
            self.pushover_api_token = api_token
            
            # Clear any previous status
            update_status("Sending test notification...", False)
            settings_window.update()
            
            # Send a test notification
            test_time = datetime.now().strftime("%H:%M:%S")
            test_result = self.send_pushover_notification(
                "Sprint Timer Test", 
                f"This is a test notification from Sprint Timer.\nSent at: {test_time}"
            )
            
            if test_result:
                update_status("✓ Test notification sent successfully!", False)
                self.pushover_enabled.set(True)  # Auto-enable if test is successful
            else:
                update_status("✗ Failed to send test notification. Please check your credentials.", True)
        
        test_button = ttk.Button(button_frame, text="Test Notification", command=test_pushover)
        test_button.pack(side="left", padx=5)
        
        # Save button
        def save_settings():
            user_key = user_key_entry.get().strip()
            api_token = api_token_entry.get().strip()
            
            if not user_key or not api_token:
                update_status("Please enter both User Key and API Token", True)
                return
                
            self.pushover_user_key = user_key
            self.pushover_api_token = api_token
            self.append_to_console("Pushover settings updated")
            settings_window.destroy()
        
        save_button = ttk.Button(button_frame, text="Save", command=save_settings)
        save_button.pack(side="left", padx=5)
        
        # Cancel button
        cancel_button = ttk.Button(button_frame, text="Cancel", command=settings_window.destroy)
        cancel_button.pack(side="left", padx=5)
        
        # Help link
        help_text = ttk.Label(settings_frame, 
                             text="Don't have Pushover? Visit pushover.net to create an account.",
                             foreground="blue", cursor="hand2")
        help_text.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))
        
        # Make the help text clickable
        def open_pushover_website(event):
            webbrowser.open_new("https://pushover.net")
        
        help_text.bind("<Button-1>", open_pushover_website)
    
    def send_pushover_notification(self, title, message):
        """Send a notification to Pushover"""
        if not self.pushover_enabled.get():
            return True  # Silently succeed if notifications are disabled
        
        if not self.pushover_user_key or not self.pushover_api_token or self.pushover_user_key == "YOUR_USER_KEY":
            self.append_to_console("Pushover credentials not configured")
            return False
        
        try:
            self.append_to_console(f"Sending Pushover notification: {title} - {message}")
            
            # Create an unverified context - only use this for personal projects!
            ssl_context = ssl._create_unverified_context()
            
            conn = http.client.HTTPSConnection("api.pushover.net:443", context=ssl_context)
            conn.request("POST", "/1/messages.json",
                         urllib.parse.urlencode({
                             "token": self.pushover_api_token,
                             "user": self.pushover_user_key,
                             "title": title,
                             "message": message,
                             "priority": 0,
                         }), {"Content-type": "application/x-www-form-urlencoded"})
            response = conn.getresponse()
            result = response.read()
            conn.close()
            
            # Log the raw response for debugging
            self.append_to_console(f"Pushover API response: {result.decode('utf-8')}")
            
            try:
                response_data = json.loads(result.decode("utf-8"))
                if response_data.get("status") == 1:
                    self.append_to_console("Pushover notification sent successfully")
                    return True
                else:
                    self.append_to_console(f"Failed to send Pushover notification: {response_data}")
                    return False
            except json.JSONDecodeError:
                self.append_to_console(f"Failed to parse Pushover API response: {result.decode('utf-8')}")
                return False
                
        except Exception as e:
            self.append_to_console(f"Error sending Pushover notification: {str(e)}")
            return False
    
    def append_to_console(self, message):
        """Add a message to the console output"""
        self.console_text.configure(state="normal")
        self.console_text.insert(tk.END, f"{message}\n")
        self.console_text.see(tk.END)  # Scroll to the end
        self.console_text.configure(state="disabled")
        logger.info(message)  # Also log to the console
    
    def toggle_auto_reset(self):
        """Toggle the auto-reset feature"""
        if self.auto_reset.get():
            self.append_to_console("Auto-reset enabled")
        else:
            self.append_to_console("Auto-reset disabled")
    
    def toggle_pushover(self):
        """Toggle the Pushover notification feature"""
        if self.pushover_enabled.get():
            self.append_to_console("Pushover notifications enabled")
            if not self.pushover_user_key or not self.pushover_api_token or self.pushover_user_key == "YOUR_USER_KEY":
                self.append_to_console("Pushover credentials not configured. Please set them in Pushover Settings.")
        else:
            self.append_to_console("Pushover notifications disabled")
    
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
    
    def clear_session_stats(self):
        """Clear the session statistics"""
        self.session_sprints = []
        self.session_top_speed = 0.0
        self.session_top_speed_time = 0.0
        self.session_best_time = float('inf')
        
        # Update displays
        self.session_speed_display.config(text="0.0 km/h")
        self.session_time_display.config(text="(00.000s)")
        
        # Clear the treeview
        for item in self.sprints_tree.get_children():
            self.sprints_tree.delete(item)
        
        self.append_to_console("Session statistics cleared")
    
    def scan_for_devices(self):
        """Scan for Bluetooth devices"""
        self.update_status("Scanning for SmartHub...")
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
        
        # Look for potential SmartHub devices (filter for likely names)
        likely_hubs = []
        for name in device_names:
            if any(keyword in name.lower() for keyword in ["smart", "hub", "speed", "veld", "fusion"]):
                likely_hubs.append(name)
                self.append_to_console(f"Potential SmartHub device: {name}")
        
        # Update the dropdown with all devices, but put likely hubs at the top
        sorted_devices = likely_hubs + [name for name in device_names if name not in likely_hubs]
        self.hub_combo['values'] = sorted_devices
        
        if sorted_devices:
            self.hub_combo.current(0)
            self.append_to_console(f"Updated device list with {len(device_names)} devices")
        
        self.update_status(f"Found {len(device_names)} devices")
    
    def connect_to_hub(self):
        """Connect to the selected SmartHub"""
        # Check if we're already connected
        if self.smart_hub and hasattr(self.smart_hub, 'is_connected') and self.smart_hub.is_connected:
            # Disconnect
            self.append_to_console("Disconnecting from SmartHub...")
            threading.Thread(target=self._disconnect_hub_thread, daemon=True).start()
            return
        
        # Connect to a new device
        selected = self.hub_var.get()
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
        
        self.append_to_console(f"Starting connection thread for SmartHub")
        self.connect_button.configure(state="disabled")
        threading.Thread(target=self._connect_hub_thread, args=(device,), daemon=True).start()
    
    def _disconnect_hub_thread(self):
        """Thread function to disconnect from the SmartHub"""
        async def disconnect():
            try:
                if self.smart_hub and self.smart_hub.is_connected:
                    # Unsubscribe from notifications if we have them
                    if self.notification_char:
                        await self.smart_hub.stop_notify(self.notification_char)
                        self.append_to_console("Unsubscribed from notifications")
                    
                    await self.smart_hub.disconnect()
                    self.append_to_console("Disconnected from SmartHub")
                    return True
            except Exception as e:
                self.append_to_console(f"Error during disconnect: {str(e)}")
                raise
        
        try:
            success = asyncio.run(disconnect())
            
            # Update the UI from the main thread
            def update_ui():
                self.smart_hub = None
                self.notification_char = None
                self.connection_indicator.configure(text="Disconnected", foreground="red")
                self.connect_button.configure(text="Connect to SmartHub", state="normal")
                self.update_status("Disconnected from SmartHub")
            
            self.root.after(0, update_ui)
        except Exception as e:
            error_msg = f"Error disconnecting: {str(e)}"
            self.root.after(0, lambda: self.update_status(error_msg))
            self.root.after(0, lambda: self.connect_button.configure(state="normal"))
            self.append_to_console(f"EXCEPTION in disconnect thread: {error_msg}")
    
    def _connect_hub_thread(self, device):
        """Thread function to connect to the SmartHub"""
        self.append_to_console(f"Connection thread started for SmartHub: {device.address}")
        
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
                
                # Store all services and characteristics for later reference
                all_services = {}
                potential_notify_chars = []
                
                for service in client.services:
                    self.append_to_console(f"Service found: {service.uuid}")
                    characteristics = []
                    
                    for char in service.characteristics:
                        properties = []
                        if "read" in char.properties:
                            properties.append("read")
                        if "write" in char.properties:
                            properties.append("write")
                        if "notify" in char.properties:
                            properties.append("notify")
                            potential_notify_chars.append(char.uuid)
                        
                        char_info = f"{char.uuid}: {', '.join(properties)}"
                        characteristics.append(char_info)
                        self.append_to_console(f"  Characteristic: {char_info}")
                    
                    all_services[service.uuid] = characteristics
                
                # Try to subscribe to each potential notification characteristic
                notification_char = None
                
                for char_uuid in potential_notify_chars:
                    try:
                        self.append_to_console(f"Trying to subscribe to notifications on: {char_uuid}")
                        
                        # Define a notification handler
                        def notification_handler(sender, data):
                            # Process in the main thread to avoid threading issues
                            self.root.after(0, lambda: self.process_notification(data))
                        
                        await client.start_notify(char_uuid, notification_handler)
                        self.append_to_console(f"Successfully subscribed to notifications on: {char_uuid}")
                        notification_char = char_uuid
                        break
                    except Exception as e:
                        self.append_to_console(f"Failed to subscribe to {char_uuid}: {str(e)}")
                
                if not notification_char:
                    self.append_to_console("WARNING: Could not find a suitable notification characteristic.")
                    self.append_to_console("You may need to manually identify the correct characteristic UUID.")
                
                return client, notification_char, all_services
                
            except Exception as e:
                self.append_to_console(f"Connection error: {str(e)}")
                raise Exception(f"Connection error: {str(e)}")
        
        try:
            client, notification_char, services = asyncio.run(connect())
            
            # Update the UI from the main thread
            def update_ui():
                self.smart_hub = client
                self.notification_char = notification_char
                self.connection_indicator.configure(text="Connected", foreground="green")
                self.connect_button.configure(text="Disconnect", state="normal")
                self.update_status("Connected to SmartHub")
                
                # Store the services for future reference
                self.append_to_console("Services for SmartHub:")
                for service_uuid, characteristics in services.items():
                    self.append_to_console(f"  Service: {service_uuid}")
                    for char in characteristics:
                        self.append_to_console(f"    Characteristic: {char}")
            
            self.root.after(0, update_ui)
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda: self.update_status(error_msg))
            self.root.after(0, lambda: self.connect_button.configure(state="normal"))
            self.append_to_console(f"EXCEPTION in connection thread: {error_msg}")
    
    def process_notification(self, data):
        """Process notification data received from the SmartHub"""
        # Convert bytes to hex for logging
        hex_data = data.hex()
        self.append_to_console(f"Notification received: {hex_data}")
        
        # Get the current lane
        try:
            current_lane = int(self.lane_var.get())
        except ValueError:
            current_lane = 1
        
        # TODO: Parse the data to determine if this is a start or end gate trigger
        # This will depend on the specific protocol used by your SmartHub
        # For now, we'll use a very simple example based on the first byte
        
        # EXAMPLE - This is placeholder logic and will need to be adjusted
        if len(data) > 0:
            # This is just an example - you'll need to analyze the actual data format
            event_type = data[0] if len(data) > 0 else 0
            lane = data[1] if len(data) > 1 else current_lane
            
            # Check if this is for our selected lane
            if lane != current_lane:
                self.append_to_console(f"Ignoring event for lane {lane} (we're monitoring lane {current_lane})")
                return
            
            if event_type == 0x01 or event_type <= 0x10:  # Example: assume low values are start events
                # If we're already timing and auto-reset is enabled, reset before starting a new sprint
                if self.is_timing and self.auto_reset.get():
                    self.append_to_console("Auto-resetting timer for new sprint")
                    self.reset_timer()
                
                self.handle_start_event()
            elif event_type == 0x02 or event_type >= 0x80:  # Example: assume high values are end events
                self.handle_end_event()
            else:
                self.append_to_console(f"Unknown event type: {event_type}")
    
    def handle_start_event(self):
        """Handle a start gate event"""
        self.append_to_console("Start gate event detected")
        self.start_time = time.time()
        self.is_timing = True
        self.start_timer_updates()
        self.update_status("Timer started")
    
    def handle_end_event(self):
        """Handle an end gate event"""
        if not self.is_timing:
            self.update_status("End event received but timer not running")
            self.append_to_console("End gate event ignored - timer not running")
            return
        
        self.append_to_console("End gate event detected")
        end_time = time.time()
        elapsed_time = end_time - self.start_time
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
            
            # Update statistics
            self.update_statistics(elapsed_time, speed_kmh, distance)
            
            # Send Pushover notification if enabled
            if self.pushover_enabled.get():
                notification_title = "Sprint Timer Result"
                # Make sure time and speed are prominently displayed in the notification
                notification_message = f"Time: {elapsed_time:.3f} seconds\nSpeed: {speed_kmh:.1f} km/h\nDistance: {distance}m"
                
                # Include additional context if available
                timestamp = datetime.now().strftime("%H:%M:%S")
                notification_message += f"\nRecorded at: {timestamp}"
                
                # Add information about records if applicable
                if speed_kmh >= self.session_top_speed:
                    notification_message += "\n[New session top speed!]"
                if speed_kmh >= self.top_speed:
                    notification_message += "\n[New all-time top speed!]"
                
                # Send the notification
                sent = self.send_pushover_notification(notification_title, notification_message)
                if not sent:
                    self.append_to_console("Failed to send sprint result to Pushover")
            
            result_msg = f"Sprint completed: {elapsed_time:.3f}s, {speed_kmh:.1f} km/h"
            self.update_status(result_msg)
            self.append_to_console(result_msg)
            
            # If auto-reset is enabled, prepare for the next sprint after a brief delay
            if self.auto_reset.get():
                self.root.after(5000, self.prepare_for_next_sprint)  # 5 second delay before ready for next sprint
                
        except ValueError:
            error_msg = "Invalid distance value"
            self.update_status(error_msg)
            self.append_to_console(error_msg)
    
    def update_statistics(self, elapsed_time, speed_kmh, distance):
        """Update all statistics with new sprint data"""
        # Create timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add to session sprints list
        sprint_data = {
            "time": elapsed_time,
            "speed": speed_kmh,
            "distance": distance,
            "timestamp": timestamp
        }
        self.session_sprints.append(sprint_data)
        
        # Update session top speed
        if speed_kmh > self.session_top_speed:
            self.session_top_speed = speed_kmh
            self.session_top_speed_time = elapsed_time
            self.session_speed_display.config(text=f"{speed_kmh:.1f} km/h")
            self.session_time_display.config(text=f"({elapsed_time:.3f}s)")
        
        # Update all-time top speed
        if speed_kmh > self.top_speed:
            self.top_speed = speed_kmh
            self.top_speed_time = elapsed_time
            self.top_speed_display.config(text=f"{speed_kmh:.1f} km/h")
            self.top_speed_time_display.config(text=f"({elapsed_time:.3f}s)")
        
        # Update best time if this is for the same distance
        if self.session_best_time == float('inf') or elapsed_time < self.session_best_time:
            self.session_best_time = elapsed_time
        
        # Add to treeview
        self.sprints_tree.insert("", 0, values=(
            f"{elapsed_time:.3f}", 
            timestamp, 
            f"{distance}", 
            f"{speed_kmh:.1f}"
        ))
        
        # Keep only the most recent 20 entries
        if len(self.sprints_tree.get_children()) > 20:
            oldest = self.sprints_tree.get_children()[-1]
            self.sprints_tree.delete(oldest)
    
    def prepare_for_next_sprint(self):
        """Prepare the timer for the next sprint"""
        # Reset only if not already timing
        if not self.is_timing:
            self.time_display.config(text="00.000")
            self.speed_display.config(text="0.0")
            self.update_status("Ready for next sprint")
            self.append_to_console("Timer ready for next sprint")
    
    def test_start_gate(self):
        """Simulate a start gate trigger for testing"""
        self.append_to_console("Test start gate triggered")
        self.handle_start_event()
    
    def test_end_gate(self):
        """Simulate an end gate trigger for testing"""
        self.append_to_console("Test end gate triggered")
        self.handle_end_event()
    
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
        
        # Disconnect BLE client
        async def disconnect():
            if self.smart_hub and self.smart_hub.is_connected:
                try:
                    if self.notification_char:
                        await self.smart_hub.stop_notify(self.notification_char)
                    await self.smart_hub.disconnect()
                except:
                    pass
        
        if self.smart_hub:
            try:
                self.append_to_console("Running disconnect routines")
                asyncio.run(disconnect())
            except Exception as e:
                self.append_to_console(f"Error during disconnect: {str(e)}")
        
        self.append_to_console("Goodbye!")
        logger.info("Application closing")
        self.root.destroy()

if __name__ == "__main__":
    logger.info("Starting SmartSpeed Timer Application")
    
    try:
        # Create the Tkinter root window
        root = tk.Tk()
        
        # Create the application
        app = SprintTimerApp(root)
        
        # Start the Tkinter main loop
        logger.info("Entering Tkinter main loop")
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        if 'root' in locals() and root:
            messagebox.showerror("Critical Error", f"An unhandled error occurred: {str(e)}")