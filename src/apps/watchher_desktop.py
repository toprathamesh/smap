#!/usr/bin/env python3
"""
WatchHer — Intelligent Public Safety Monitoring System
Desktop Application for Women's Safety Surveillance

Features:
- Real-time women's safety monitoring
- Lone/surrounded women detection
- Distress signal recognition
- Threat level assessment
- Risk zone heatmaps for urban planning
- Safety alerts and notifications

Version: 2.0
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import time
import threading
from datetime import datetime
import json
import os
from collections import defaultdict, deque

class WatchHerDesktopApp:
    """WatchHer — Intelligent Public Safety Monitoring System"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("WatchHer — Women's Safety Monitoring System")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#2c3e50')
        
        # Application state
        self.ai_analyzer = None
        self.is_processing = False
        self.cap = None
        self.video_thread = None
        
        # WatchHer statistics
        self.total_women_monitored = 0
        self.total_safety_alerts = 0
        self.lone_women_incidents = 0
        self.surrounded_women_incidents = 0
        self.distress_signals_detected = 0
        self.current_threat_level = 'SAFE'
        
        # Risk zone heatmap data
        self.risk_zones = defaultdict(int)  # {(x_grid, y_grid): risk_level}
        self.heatmap_grid_size = 50  # Grid cell size for heatmap
        self.risk_history = deque(maxlen=1000)  # Store recent risk events
        
        # Frame tracking
        self.frames_processed = 0
        self.start_time = time.time()
        
        # UI Variables
        self.file_path = tk.StringVar()
        self.current_status = tk.StringVar(value="WatchHer System Ready")
        self.threat_level_var = tk.StringVar(value="SAFE")
        
        self.initialize_ai()
        self.create_interface()
    
    def initialize_ai(self):
        """Initialize AI analyzer in background"""
        def ai_init_worker():
            try:
                from src.core.ai_analyzer import AIAnalyzer
                self.ai_analyzer = AIAnalyzer()
                self.root.after(0, self.ai_initialization_complete)
            except Exception as e:
                self.root.after(0, lambda: self.add_log(f"❌ AI initialization failed: {e}", "red"))
        
        threading.Thread(target=ai_init_worker, daemon=True).start()
        self.add_log("🔄 Initializing WatchHer AI system...")
    
    def ai_initialization_complete(self):
        """Called when AI initialization is complete"""
        self.add_log("✅ WatchHer AI system ready for women's safety monitoring")
        self.current_status.set("AI System Ready - Select source and start monitoring")
    
    def create_interface(self):
        """Create the main interface"""
        # Create main frames
        self.create_header_panel()
        self.create_main_content()
        self.create_status_bar()
    
    def create_header_panel(self):
        """Create header with WatchHer branding"""
        header_frame = tk.Frame(self.root, bg='#34495e', height=80)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        # WatchHer logo and title
        title_label = tk.Label(header_frame, text="WatchHer", 
                              font=('Arial', 24, 'bold'), 
                              fg='#e74c3c', bg='#34495e')
        title_label.pack(side='left', padx=20, pady=15)
        
        subtitle_label = tk.Label(header_frame, text="Intelligent Public Safety Monitoring for Women's Protection", 
                                 font=('Arial', 12), 
                                 fg='#ecf0f1', bg='#34495e')
        subtitle_label.pack(side='left', padx=10, pady=20)
        
        # Real-time threat level indicator
        self.threat_frame = tk.Frame(header_frame, bg='#27ae60', padx=10, pady=5)
        self.threat_frame.pack(side='right', padx=20, pady=15)
        
        tk.Label(self.threat_frame, text="THREAT LEVEL:", 
                font=('Arial', 10, 'bold'), fg='white', bg='#27ae60').pack()
        self.threat_label = tk.Label(self.threat_frame, textvariable=self.threat_level_var,
                                    font=('Arial', 14, 'bold'), fg='white', bg='#27ae60')
        self.threat_label.pack()
    
    def create_main_content(self):
        """Create main content area"""
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel - Video and controls
        left_panel = tk.Frame(main_frame, bg='#34495e', width=800)
        left_panel.pack(side='left', fill='both', expand=True, padx=5)
        
        # Right panel - Statistics and monitoring
        right_panel = tk.Frame(main_frame, bg='#34495e', width=400)
        right_panel.pack(side='right', fill='both', padx=5)
        
        self.create_video_panel(left_panel)
        self.create_control_panel(left_panel)
        self.create_monitoring_panel(right_panel)
        self.create_heatmap_panel(right_panel)
    
    def create_video_panel(self, parent):
        """Create video display panel"""
        video_frame = tk.LabelFrame(parent, text="Live Safety Monitoring", 
                                   font=('Arial', 12, 'bold'),
                                   fg='#ecf0f1', bg='#34495e')
        video_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Video display
        self.video_label = tk.Label(video_frame, 
                                   text="WatchHer Video Display\nClick 'Start Monitoring' to begin",
                                   font=('Arial', 14), 
                                   fg='#95a5a6', bg='#2c3e50',
                                   width=60, height=20)
        self.video_label.pack(padx=10, pady=10, expand=True)
    
    def create_control_panel(self, parent):
        """Create control panel"""
        control_frame = tk.LabelFrame(parent, text="Monitoring Controls", 
                                     font=('Arial', 12, 'bold'),
                                     fg='#ecf0f1', bg='#34495e')
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Source selection
        source_frame = tk.Frame(control_frame, bg='#34495e')
        source_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(source_frame, text="Video Source:", 
                font=('Arial', 10), fg='#ecf0f1', bg='#34495e').pack(side='left')
        
        self.source_var = tk.StringVar(value="webcam")
        tk.Radiobutton(source_frame, text="Live Webcam", variable=self.source_var, value="webcam",
                      fg='#ecf0f1', bg='#34495e', selectcolor='#34495e').pack(side='left', padx=10)
        tk.Radiobutton(source_frame, text="Video File", variable=self.source_var, value="file",
                      fg='#ecf0f1', bg='#34495e', selectcolor='#34495e').pack(side='left', padx=10)
        
        # File selection
        file_frame = tk.Frame(control_frame, bg='#34495e')
        file_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Entry(file_frame, textvariable=self.file_path, width=40).pack(side='left', padx=5)
        tk.Button(file_frame, text="Browse", command=self.browse_file,
                 bg='#3498db', fg='white', padx=10).pack(side='left', padx=5)
        
        # Control buttons
        button_frame = tk.Frame(control_frame, bg='#34495e')
        button_frame.pack(fill='x', padx=10, pady=10)
        
        self.start_btn = tk.Button(button_frame, text="🔴 Start Monitoring", 
                                  command=self.start_monitoring,
                                  bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                  padx=20, pady=5)
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(button_frame, text="⏹️ Stop Monitoring", 
                                 command=self.stop_monitoring,
                                 bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                                 padx=20, pady=5, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        tk.Button(button_frame, text="📊 Generate Report", 
                 command=self.generate_safety_report,
                 bg='#9b59b6', fg='white', font=('Arial', 12),
                 padx=15, pady=5).pack(side='left', padx=5)
    
    def create_monitoring_panel(self, parent):
        """Create real-time monitoring panel"""
        monitor_frame = tk.LabelFrame(parent, text="Safety Monitoring Dashboard", 
                                     font=('Arial', 12, 'bold'),
                                     fg='#ecf0f1', bg='#34495e')
        monitor_frame.pack(fill='x', padx=5, pady=5)
        
        # Current status
        self.status_label = tk.Label(monitor_frame, textvariable=self.current_status,
                                    font=('Arial', 11), fg='#ecf0f1', bg='#34495e',
                                    wraplength=350)
        self.status_label.pack(pady=5)
        
        # Safety statistics
        stats_frame = tk.Frame(monitor_frame, bg='#34495e')
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        # Women monitoring stats
        self.women_stats = tk.Label(stats_frame, text="👩 Women Monitored: 0",
                                   font=('Arial', 10), fg='#e67e22', bg='#34495e')
        self.women_stats.pack(anchor='w')
        
        self.alert_stats = tk.Label(stats_frame, text="🚨 Safety Alerts: 0",
                                   font=('Arial', 10), fg='#e74c3c', bg='#34495e')
        self.alert_stats.pack(anchor='w')
        
        self.lone_stats = tk.Label(stats_frame, text="⚠️ Lone Women: 0",
                                  font=('Arial', 10), fg='#f39c12', bg='#34495e')
        self.lone_stats.pack(anchor='w')
        
        self.surrounded_stats = tk.Label(stats_frame, text="🔴 Surrounded Women: 0",
                                        font=('Arial', 10), fg='#e74c3c', bg='#34495e')
        self.surrounded_stats.pack(anchor='w')
        
        self.distress_stats = tk.Label(stats_frame, text="🆘 Distress Signals: 0",
                                      font=('Arial', 10), fg='#9b59b6', bg='#34495e')
        self.distress_stats.pack(anchor='w')
        
        # Performance stats
        perf_frame = tk.Frame(monitor_frame, bg='#34495e')
        perf_frame.pack(fill='x', padx=10, pady=5)
        
        self.fps_label = tk.Label(perf_frame, text="⚡ FPS: 0.0",
                                 font=('Arial', 10), fg='#2ecc71', bg='#34495e')
        self.fps_label.pack(anchor='w')
        
        self.frames_label = tk.Label(perf_frame, text="📸 Frames: 0",
                                    font=('Arial', 10), fg='#3498db', bg='#34495e')
        self.frames_label.pack(anchor='w')
        
        # Activity log
        log_frame = tk.LabelFrame(monitor_frame, text="Activity Log", 
                                 font=('Arial', 10, 'bold'),
                                 fg='#ecf0f1', bg='#34495e')
        log_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=45, 
                               bg='#2c3e50', fg='#ecf0f1',
                               font=('Courier', 9))
        log_scrollbar = tk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')
    
    def create_heatmap_panel(self, parent):
        """Create risk zone heatmap panel for urban planning"""
        heatmap_frame = tk.LabelFrame(parent, text="Risk Zone Heatmap (Urban Planning)", 
                                     font=('Arial', 12, 'bold'),
                                     fg='#ecf0f1', bg='#34495e')
        heatmap_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Heatmap canvas
        self.heatmap_canvas = tk.Canvas(heatmap_frame, width=350, height=250,
                                       bg='#2c3e50', highlightthickness=0)
        self.heatmap_canvas.pack(padx=10, pady=10)
        
        # Heatmap controls
        heatmap_controls = tk.Frame(heatmap_frame, bg='#34495e')
        heatmap_controls.pack(fill='x', padx=10, pady=5)
        
        tk.Button(heatmap_controls, text="📊 Update Heatmap", 
                 command=self.update_heatmap,
                 bg='#16a085', fg='white', font=('Arial', 10)).pack(side='left', padx=5)
        
        tk.Button(heatmap_controls, text="💾 Export Heatmap", 
                 command=self.export_heatmap,
                 bg='#8e44ad', fg='white', font=('Arial', 10)).pack(side='left', padx=5)
        
        tk.Button(heatmap_controls, text="🗑️ Clear Data", 
                 command=self.clear_heatmap,
                 bg='#c0392b', fg='white', font=('Arial', 10)).pack(side='left', padx=5)
    
    def create_status_bar(self):
        """Create status bar"""
        status_frame = tk.Frame(self.root, bg='#34495e', height=30)
        status_frame.pack(fill='x', padx=5, pady=2)
        status_frame.pack_propagate(False)
        
        self.status_bar = tk.Label(status_frame, text="WatchHer System Ready",
                                  font=('Arial', 9), fg='#95a5a6', bg='#34495e')
        self.status_bar.pack(side='left', padx=10, pady=5)
        
        # System uptime
        self.uptime_label = tk.Label(status_frame, text="Uptime: 00:00:00",
                                    font=('Arial', 9), fg='#95a5a6', bg='#34495e')
        self.uptime_label.pack(side='right', padx=10, pady=5)
        
        # Update uptime every second
        self.update_uptime()
    
    def update_uptime(self):
        """Update uptime display"""
        uptime = time.time() - self.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        self.uptime_label.config(text=f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
        self.root.after(1000, self.update_uptime)
    
    def start_monitoring(self):
        """Start WatchHer monitoring"""
        if not self.ai_analyzer or not self.ai_analyzer.is_ready():
            messagebox.showerror("Error", "AI system not ready. Please wait for initialization.")
            return
        
        self.is_processing = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        if self.source_var.get() == "webcam":
            self.start_webcam_monitoring()
        else:
            if not self.file_path.get():
                messagebox.showerror("Error", "Please select a video file.")
                self.stop_monitoring()
                return
            self.start_file_monitoring()
        
        self.add_log("🔴 WatchHer monitoring started")
        self.current_status.set("Monitoring active - Analyzing for women's safety")
    
    def start_webcam_monitoring(self):
        """Start webcam monitoring"""
        def webcam_worker():
            try:
                self.cap = cv2.VideoCapture(0)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                
                while self.is_processing:
                    ret, frame = self.cap.read()
                    if ret:
                        self.process_frame(frame)
                    time.sleep(0.033)  # ~30 FPS
                
                self.cap.release()
            except Exception as e:
                self.root.after(0, lambda: self.add_log(f"❌ Webcam error: {e}", "red"))
        
        self.video_thread = threading.Thread(target=webcam_worker, daemon=True)
        self.video_thread.start()
    
    def start_file_monitoring(self):
        """Start video file monitoring"""
        def file_worker():
            try:
                self.cap = cv2.VideoCapture(self.file_path.get())
                
                while self.is_processing:
                    ret, frame = self.cap.read()
                    if not ret:
                        # Loop video
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    
                    self.process_frame(frame)
                    time.sleep(0.033)  # ~30 FPS
                
                self.cap.release()
            except Exception as e:
                self.root.after(0, lambda: self.add_log(f"❌ Video file error: {e}", "red"))
        
        self.video_thread = threading.Thread(target=file_worker, daemon=True)
        self.video_thread.start()
    
    def process_frame(self, frame):
        """Process frame with WatchHer analysis"""
        try:
            # Flip webcam frame for natural view
            if self.source_var.get() == "webcam":
                frame = cv2.flip(frame, 1)
            
            # Resize for processing
            process_frame = cv2.resize(frame, (640, 480))
            
            # **WatchHer AI Analysis**
            people, weapons, safety_analysis = self.ai_analyzer.analyze_frame(process_frame)
            
            # Scale detections back to display size
            display_frame = cv2.resize(frame, (800, 600))
            scale_x = 800 / 640
            scale_y = 600 / 480
            
            # Scale detections
            for person in people:
                bbox = person['bbox']
                person['bbox'] = [int(bbox[0] * scale_x), int(bbox[1] * scale_y),
                                 int(bbox[2] * scale_x), int(bbox[3] * scale_y)]
            
            for weapon in weapons:
                bbox = weapon['bbox']
                weapon['bbox'] = [int(bbox[0] * scale_x), int(bbox[1] * scale_y),
                                 int(bbox[2] * scale_x), int(bbox[3] * scale_y)]
            
            # Draw WatchHer visualizations
            display_frame = self.ai_analyzer.draw_detections(display_frame, people, weapons)
            display_frame = self.ai_analyzer.draw_safety_overlay(display_frame, safety_analysis)
            
            # Update statistics
            self.update_statistics(people, weapons, safety_analysis)
            
            # Update risk zones for heatmap
            self.update_risk_zones(people, safety_analysis, display_frame.shape)
            
            # Update display
            self.update_display(display_frame)
            
            self.frames_processed += 1
            
        except Exception as e:
            self.add_log(f"❌ Frame processing error: {e}", "red")
    
    def update_statistics(self, people, weapons, safety_analysis):
        """Update WatchHer statistics"""
        # Count women and safety events
        women_count = len([p for p in people if p.get('gender') == 'woman'])
        self.total_women_monitored += women_count
        
        # Safety alerts
        lone_women = len(safety_analysis.get('lone_women', []))
        surrounded_women = len(safety_analysis.get('surrounded_women', []))
        women_in_danger = len(safety_analysis.get('women_in_danger', []))
        distress_signals = len(safety_analysis.get('distress_signals', []))
        
        self.lone_women_incidents += lone_women
        self.surrounded_women_incidents += surrounded_women
        self.distress_signals_detected += distress_signals
        
        total_alerts = lone_women + surrounded_women + women_in_danger + distress_signals
        self.total_safety_alerts += total_alerts
        
        # Update threat level
        self.current_threat_level = safety_analysis.get('overall_threat_level', 'SAFE')
        
        # Log significant events
        if women_in_danger > 0:
            self.add_log(f"🚨 CRITICAL: {women_in_danger} women in immediate danger!", "red")
        elif surrounded_women > 0:
            self.add_log(f"⚠️ ALERT: {surrounded_women} women surrounded", "orange")
        elif distress_signals > 0:
            self.add_log(f"🆘 DISTRESS: {distress_signals} distress signals", "orange")
        elif lone_women > 0:
            self.add_log(f"ℹ️ INFO: {lone_women} women alone", "blue")
        
        # Update UI
        self.root.after(0, self.update_ui_statistics)
    
    def update_ui_statistics(self):
        """Update UI statistics display"""
        # Update threat level indicator
        self.threat_level_var.set(self.current_threat_level)
        
        # Color code threat level
        if self.current_threat_level == 'CRITICAL':
            self.threat_frame.config(bg='#e74c3c')
            self.threat_label.config(bg='#e74c3c')
        elif self.current_threat_level == 'HIGH':
            self.threat_frame.config(bg='#e67e22')
            self.threat_label.config(bg='#e67e22')
        elif self.current_threat_level == 'MODERATE':
            self.threat_frame.config(bg='#f39c12')
            self.threat_label.config(bg='#f39c12')
        elif self.current_threat_level == 'LOW':
            self.threat_frame.config(bg='#f1c40f')
            self.threat_label.config(bg='#f1c40f')
        else:
            self.threat_frame.config(bg='#27ae60')
            self.threat_label.config(bg='#27ae60')
        
        # Update statistics
        self.women_stats.config(text=f"👩 Women Monitored: {self.total_women_monitored}")
        self.alert_stats.config(text=f"🚨 Safety Alerts: {self.total_safety_alerts}")
        self.lone_stats.config(text=f"⚠️ Lone Women: {self.lone_women_incidents}")
        self.surrounded_stats.config(text=f"🔴 Surrounded Women: {self.surrounded_women_incidents}")
        self.distress_stats.config(text=f"🆘 Distress Signals: {self.distress_signals_detected}")
        
        # Calculate FPS
        if self.frames_processed > 0:
            elapsed = time.time() - self.start_time
            fps = self.frames_processed / elapsed if elapsed > 0 else 0
            self.fps_label.config(text=f"⚡ FPS: {fps:.1f}")
        
        self.frames_label.config(text=f"📸 Frames: {self.frames_processed}")
    
    def update_risk_zones(self, people, safety_analysis, frame_shape):
        """Update risk zone heatmap data"""
        h, w = frame_shape[:2]
        
        # Add risk events to heatmap
        for person in people:
            x1, y1, x2, y2 = person['bbox']
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # Convert to grid coordinates
            grid_x = center_x // self.heatmap_grid_size
            grid_y = center_y // self.heatmap_grid_size
            
            # Base risk for any person
            risk_level = 1
            
            # Higher risk for women
            if person.get('gender') == 'woman':
                risk_level += 2
            
            # Much higher risk for safety events
            if person.get('has_harmful_object'):
                risk_level += 10
            
            self.risk_zones[(grid_x, grid_y)] += risk_level
        
        # Add specific safety alerts to heatmap
        threat_level = safety_analysis.get('overall_threat_level', 'SAFE')
        if threat_level in ['HIGH', 'CRITICAL']:
            # Add risk to entire current view
            for x in range(0, w // self.heatmap_grid_size):
                for y in range(0, h // self.heatmap_grid_size):
                    if threat_level == 'CRITICAL':
                        self.risk_zones[(x, y)] += 5
                    else:
                        self.risk_zones[(x, y)] += 2
        
        # Store risk event for history
        self.risk_history.append({
            'timestamp': datetime.now(),
            'threat_level': threat_level,
            'women_count': len([p for p in people if p.get('gender') == 'woman']),
            'safety_alerts': len(safety_analysis.get('lone_women', [])) + 
                           len(safety_analysis.get('surrounded_women', [])) + 
                           len(safety_analysis.get('women_in_danger', []))
        })
    
    def update_heatmap(self):
        """Update risk zone heatmap visualization"""
        self.heatmap_canvas.delete("all")
        
        if not self.risk_zones:
            self.heatmap_canvas.create_text(175, 125, text="No risk data available", 
                                          fill='#95a5a6', font=('Arial', 12))
            return
        
        # Find max risk for normalization
        max_risk = max(self.risk_zones.values()) if self.risk_zones else 1
        
        # Canvas dimensions
        canvas_width = 350
        canvas_height = 250
        
        # Draw grid cells
        cell_width = canvas_width // 20  # 20x15 grid
        cell_height = canvas_height // 15
        
        for (grid_x, grid_y), risk_level in self.risk_zones.items():
            if grid_x >= 20 or grid_y >= 15:  # Skip out of bounds
                continue
            
            # Normalize risk to 0-1
            normalized_risk = min(risk_level / max_risk, 1.0)
            
            # Color from green (low risk) to red (high risk)
            if normalized_risk < 0.3:
                color = f"#{int(255 * normalized_risk * 3):02x}ff00"  # Green to yellow
            elif normalized_risk < 0.7:
                ratio = (normalized_risk - 0.3) / 0.4
                green = int(255 * (1 - ratio))
                color = f"#ff{green:02x}00"  # Yellow to orange
            else:
                ratio = (normalized_risk - 0.7) / 0.3
                red = int(255 * (1 - ratio * 0.5))
                color = f"#{red:02x}0000"  # Orange to dark red
            
            # Draw cell
            x1 = grid_x * cell_width
            y1 = grid_y * cell_height
            x2 = x1 + cell_width
            y2 = y1 + cell_height
            
            self.heatmap_canvas.create_rectangle(x1, y1, x2, y2, 
                                               fill=color, outline="", 
                                               stipple="gray25" if normalized_risk < 0.2 else "")
        
        # Add legend
        self.heatmap_canvas.create_text(10, 10, text="Risk Level:", 
                                      fill='white', font=('Arial', 10, 'bold'), anchor='nw')
        
        # Legend colors
        legend_colors = ["#00ff00", "#ffff00", "#ff7f00", "#ff0000", "#7f0000"]
        legend_labels = ["Low", "Med", "High", "Very High", "Critical"]
        
        for i, (color, label) in enumerate(zip(legend_colors, legend_labels)):
            x = 10 + i * 60
            self.heatmap_canvas.create_rectangle(x, 25, x + 15, 35, fill=color, outline="white")
            self.heatmap_canvas.create_text(x + 20, 30, text=label, 
                                          fill='white', font=('Arial', 8), anchor='w')
    
    def export_heatmap(self):
        """Export heatmap data for urban planning"""
        if not self.risk_zones:
            messagebox.showwarning("Warning", "No heatmap data to export.")
            return
        
        try:
            # Create export data
            export_data = {
                'metadata': {
                    'export_time': datetime.now().isoformat(),
                    'total_frames': self.frames_processed,
                    'monitoring_duration': time.time() - self.start_time,
                    'grid_size': self.heatmap_grid_size
                },
                'risk_zones': {f"{k[0]},{k[1]}": v for k, v in self.risk_zones.items()},
                'safety_statistics': {
                    'women_monitored': self.total_women_monitored,
                    'safety_alerts': self.total_safety_alerts,
                    'lone_women_incidents': self.lone_women_incidents,
                    'surrounded_women_incidents': self.surrounded_women_incidents,
                    'distress_signals': self.distress_signals_detected
                },
                'risk_history': [
                    {
                        'timestamp': event['timestamp'].isoformat(),
                        'threat_level': event['threat_level'],
                        'women_count': event['women_count'],
                        'safety_alerts': event['safety_alerts']
                    }
                    for event in list(self.risk_history)
                ]
            }
            
            # Save to file
            filename = filedialog.asksaveasfilename(
                title="Export WatchHer Heatmap Data",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                self.add_log(f"📊 Heatmap data exported to {filename}")
                messagebox.showinfo("Success", f"Heatmap data exported successfully!")
        
        except Exception as e:
            self.add_log(f"❌ Export failed: {e}", "red")
            messagebox.showerror("Error", f"Failed to export heatmap data:\n{e}")
    
    def clear_heatmap(self):
        """Clear heatmap data"""
        if messagebox.askyesno("Confirm", "Clear all heatmap data?"):
            self.risk_zones.clear()
            self.risk_history.clear()
            self.update_heatmap()
            self.add_log("🗑️ Heatmap data cleared")
    
    def generate_safety_report(self):
        """Generate comprehensive safety report"""
        try:
            report_data = {
                'report_date': datetime.now().isoformat(),
                'monitoring_duration': time.time() - self.start_time,
                'frames_processed': self.frames_processed,
                'safety_statistics': {
                    'women_monitored': self.total_women_monitored,
                    'total_safety_alerts': self.total_safety_alerts,
                    'lone_women_incidents': self.lone_women_incidents,
                    'surrounded_women_incidents': self.surrounded_women_incidents,
                    'distress_signals_detected': self.distress_signals_detected,
                    'current_threat_level': self.current_threat_level
                },
                'risk_analysis': {
                    'high_risk_zones': len([r for r in self.risk_zones.values() if r > 10]),
                    'total_risk_zones': len(self.risk_zones),
                    'average_risk_level': sum(self.risk_zones.values()) / len(self.risk_zones) if self.risk_zones else 0
                }
            }
            
            # Create report text
            report_text = f"""
WatchHer — Women's Safety Monitoring Report
==========================================

Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Monitoring Duration: {report_data['monitoring_duration']/3600:.2f} hours
Frames Processed: {report_data['frames_processed']}

SAFETY STATISTICS
=================
👩 Total Women Monitored: {report_data['safety_statistics']['women_monitored']}
🚨 Total Safety Alerts: {report_data['safety_statistics']['total_safety_alerts']}
⚠️ Lone Women Incidents: {report_data['safety_statistics']['lone_women_incidents']}
🔴 Surrounded Women Incidents: {report_data['safety_statistics']['surrounded_women_incidents']}
🆘 Distress Signals Detected: {report_data['safety_statistics']['distress_signals_detected']}
📊 Current Threat Level: {report_data['safety_statistics']['current_threat_level']}

RISK ANALYSIS
=============
🏠 High Risk Zones: {report_data['risk_analysis']['high_risk_zones']}
📍 Total Risk Zones: {report_data['risk_analysis']['total_risk_zones']}
📈 Average Risk Level: {report_data['risk_analysis']['average_risk_level']:.2f}

RECOMMENDATIONS
===============
- Deploy additional security personnel in high-risk zones
- Improve lighting in areas with frequent lone women incidents  
- Install emergency call stations in isolated areas
- Increase patrol frequency during high-threat periods
"""
            
            # Show report
            report_window = tk.Toplevel(self.root)
            report_window.title("WatchHer Safety Report")
            report_window.geometry("600x500")
            report_window.configure(bg='#2c3e50')
            
            text_widget = tk.Text(report_window, wrap='word', 
                                 bg='#34495e', fg='#ecf0f1', 
                                 font=('Courier', 10))
            text_widget.pack(fill='both', expand=True, padx=10, pady=10)
            text_widget.insert('1.0', report_text)
            text_widget.config(state='disabled')
            
            # Save button
            save_btn = tk.Button(report_window, text="💾 Save Report", 
                               command=lambda: self.save_report(report_text),
                               bg='#27ae60', fg='white', font=('Arial', 12))
            save_btn.pack(pady=10)
            
            self.add_log("📋 Safety report generated")
            
        except Exception as e:
            self.add_log(f"❌ Report generation failed: {e}", "red")
            messagebox.showerror("Error", f"Failed to generate report:\n{e}")
    
    def save_report(self, report_text):
        """Save safety report to file"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Save WatchHer Safety Report",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write(report_text)
                self.add_log(f"💾 Report saved to {filename}")
                messagebox.showinfo("Success", f"Report saved successfully!")
        
        except Exception as e:
            self.add_log(f"❌ Report save failed: {e}", "red")
            messagebox.showerror("Error", f"Failed to save report:\n{e}")
    
    def update_display(self, frame):
        """Update video display"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            photo = ImageTk.PhotoImage(pil_image)
            
            self.root.after(0, lambda: self._update_video_label(photo))
        except Exception as e:
            self.add_log(f"❌ Display update failed: {e}", "red")
    
    def _update_video_label(self, photo):
        """Update video label"""
        self.video_label.config(image=photo, text="")
        self.video_label.image = photo
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_processing = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
        if self.cap:
            self.cap.release()
        
        self.video_label.config(image='', text="Monitoring Stopped\nClick 'Start Monitoring' to resume")
        self.video_label.image = None
        
        self.add_log("⏹️ WatchHer monitoring stopped")
        self.current_status.set("Monitoring stopped - Ready to resume")
    
    def browse_file(self):
        """Browse for video file"""
        filename = filedialog.askopenfilename(
            title="Select Video File for Analysis",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_path.set(filename)
    
    def add_log(self, message, color="white"):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.log_text.config(state='normal')
            self.log_text.insert('end', log_message)
            self.log_text.see('end')
            self.log_text.config(state='disabled')
        
        self.root.after(0, update_log)

def main():
    """Main function"""
    print("🚀 Starting WatchHer — Intelligent Public Safety Monitoring System")
    
    try:
        root = tk.Tk()
        app = WatchHerDesktopApp(root)
        root.mainloop()
    except Exception as e:
        print(f"❌ Application failed to start: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
