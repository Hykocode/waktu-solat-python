import sys
import csv
import datetime
import time
import os
import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QFileDialog, QLineEdit, QFrame,
                            QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTextEdit,
                            QGridLayout, QSpacerItem, QSizePolicy, QScrollArea)
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QRect, QEasingCurve, QSequentialAnimationGroup
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QFontDatabase

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PrayerTimesApp")

# UI Theme Constants
class UITheme:
    """Centralized theme constants for consistent UI styling"""
    # Colors
    PRIMARY_COLOR = "#3B82F6"  # Blue
    SUCCESS_COLOR = "#10B981"  # Green
    WARNING_COLOR = "#F59E0B"  # Amber
    DANGER_COLOR = "#EF4444"   # Red
    INFO_COLOR = "#60A5FA"     # Light Blue
    
    DARK_BG = "#1E293B"        # Dark background
    DARKER_BG = "#0F172A"      # Darker background
    LIGHT_BG = "#334155"       # Light background
    
    TEXT_PRIMARY = "#FFFFFF"   # White text
    TEXT_SECONDARY = "#94A3B8" # Gray text
    TEXT_ACCENT = "#FFFFFF"    # white
    
    # Prayer card colors
    PRAYER_COLORS = {
        "Imsak": "#FF5733",    # Red
        "Subuh": "#33FF57",    # Green
        "Syuruk": "#3357FF",   # Blue
        "Zohor": "#FF33A1",    # Pink
        "Asar": "#FFC300",     # Yellow
        "Maghrib": "#8E44AD",  # Purple
        "Isyak": "#1ABC9C"     # Teal
    }
    
    # Alert colors with opacity
    ALERT_AZAN = "rgba(16, 185, 129, 0.95)"    # Green with opacity
    ALERT_IQAMAH = "rgba(59, 130, 246, 0.95)"  # Blue with opacity
    ALERT_REMINDER = "rgba(245, 158, 11, 0.95)" # Amber with opacity
    
    # Font sizes
    FONT_LARGE = 32
    FONT_MEDIUM = 24
    FONT_SMALL = 18
    FONT_TINY = 14
    
    # Spacing
    PADDING_LARGE = 20
    PADDING_MEDIUM = 15
    PADDING_SMALL = 10
    PADDING_TINY = 5
    
    # Border radius
    BORDER_RADIUS_LARGE = 10
    BORDER_RADIUS_SMALL = 5
    
    # Button styles
    @staticmethod
    def primary_button_style():
        return f"""
            QPushButton {{
                background-color: {UITheme.PRIMARY_COLOR};
                color: {UITheme.TEXT_PRIMARY};
                border: none;
                border-radius: {UITheme.BORDER_RADIUS_SMALL}px;
                padding: {UITheme.PADDING_SMALL}px;
                font-size: {UITheme.FONT_TINY}px;
            }}
            QPushButton:hover {{
                background-color: #2563EB;
            }}
        """
    
    @staticmethod
    def success_button_style():
        return f"""
            QPushButton {{
                background-color: {UITheme.SUCCESS_COLOR};
                color: {UITheme.TEXT_PRIMARY};
                border: none;
                border-radius: {UITheme.BORDER_RADIUS_SMALL}px;
                padding: {UITheme.PADDING_SMALL}px;
                font-size: {UITheme.FONT_TINY}px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """
    
    @staticmethod
    def danger_button_style():
        return f"""
            QPushButton {{
                background-color: {UITheme.DANGER_COLOR};
                color: {UITheme.TEXT_PRIMARY};
                border: none;
                border-radius: {UITheme.BORDER_RADIUS_SMALL}px;
                padding: {UITheme.PADDING_SMALL}px;
                font-size: {UITheme.FONT_TINY}px;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
        """
    
    @staticmethod
    def settings_dialog_style():
        return f"""
            QWidget {{
                background-color: {UITheme.DARK_BG};
                color: {UITheme.TEXT_PRIMARY};
            }}
            QLabel {{
                font-size: {UITheme.FONT_TINY}px;
                margin-bottom: 5px;
            }}
            QLineEdit, QTableWidget {{
                background-color: {UITheme.LIGHT_BG};
                color: {UITheme.TEXT_PRIMARY};
                border: 1px solid #475569;
                border-radius: {UITheme.BORDER_RADIUS_SMALL}px;
                padding: 8px;
                font-size: {UITheme.FONT_TINY}px;
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {UITheme.PRIMARY_COLOR};
                color: {UITheme.TEXT_PRIMARY};
                padding: 8px;
                border: none;
            }}
        """

# Configuration Validator
class ConfigValidator:
    """Validates configuration values to ensure they meet expected criteria"""
    
    @staticmethod
    def validate_string(value, field_name, allow_empty=True):
        """Validate that a value is a string"""
        if not isinstance(value, str):
            logger.warning(f"Configuration error: {field_name} must be a string, got {type(value)}")
            return ""
        if not allow_empty and not value:
            logger.warning(f"Configuration error: {field_name} cannot be empty")
            return ""
        return value
    
    @staticmethod
    def validate_path(value, field_name, must_exist=False):
        """Validate that a value is a valid file path"""
        value = ConfigValidator.validate_string(value, field_name)
        if must_exist and value and not os.path.exists(value):
            logger.warning(f"Configuration error: {field_name} path does not exist: {value}")
            return ""
        return value
    
    @staticmethod
    def validate_config(config, default_config):
        """Validate the entire configuration object"""
        validated = {}
        
        # Validate mosque_name (string, can be empty)
        validated["mosque_name"] = ConfigValidator.validate_string(
            config.get("mosque_name", default_config["mosque_name"]),
            "mosque_name"
        )
        
        # Validate flash_message (string, cannot be empty)
        validated["flash_message"] = ConfigValidator.validate_string(
            config.get("flash_message", default_config["flash_message"]),
            "flash_message",
            allow_empty=False
        ) or default_config["flash_message"]
        
        # Validate background_image_path (path, doesn't need to exist)
        validated["background_image_path"] = ConfigValidator.validate_path(
            config.get("background_image_path", default_config["background_image_path"]),
            "background_image_path"
        )
        
        # Validate data_file_path (path, doesn't need to exist)
        validated["data_file_path"] = ConfigValidator.validate_path(
            config.get("data_file_path", default_config["data_file_path"]),
            "data_file_path"
        ) or default_config["data_file_path"]
        
        return validated

# Configuration Manager
class ConfigManager:
    def __init__(self):
        # Get the base directory for the application
        self.base_dir = self._get_base_dir()
        self.config_file = self.base_dir / "config.json"
        self.default_config = {
            "mosque_name": "",
            "flash_message": "Welcome to the Mosque Prayer Times Display",
            "background_image_path": "",
            "data_file_path": str(self.base_dir / "prayer_times.csv")
        }
        self.config = self.load_config()
    
    def _get_base_dir(self):
        """Get the base directory for the application."""
        # Use the directory where the script is located
        base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        # Create the directory if it doesn't exist
        base_dir.mkdir(exist_ok=True)
        return base_dir
    
    def load_config(self):
        """Load configuration from file or create default if not exists."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as file:
                    config = json.load(file)
                    # Validate and merge with default config
                    validated_config = ConfigValidator.validate_config(config, self.default_config)
                    logger.info("Configuration loaded and validated successfully.")
                    return validated_config
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing configuration file: {str(e)}")
                logger.info("Using default configuration.")
                return self.default_config.copy()
            except Exception as e:
                logger.error(f"Error loading configuration: {str(e)}")
                return self.default_config.copy()
        else:
            logger.info("No configuration file found. Using defaults.")
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """Save configuration to file."""
        if config is not None:
            # Validate config before saving
            self.config = ConfigValidator.validate_config(config, self.default_config)
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(self.config, file, indent=4)
            logger.info("Configuration saved successfully.")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value and save."""
        self.config[key] = value
        self.save_config()

# Data Manager
class PrayerTimesDataManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.prayer_times = []
        self.fallback_prayer_times = self._create_fallback_data()
        self.load_prayer_times()
    
    def _create_fallback_data(self):
        """Create fallback prayer times for today in case loading fails"""
        today = datetime.datetime.now()
        today_str = today.strftime("%d/%m/%Y")
        hijri_date = "Unknown"  # In a real app, you'd calculate this
        day_name = today.strftime("%A")
        
        # Default prayer times (just placeholders)
        return [{
            "Tarikh Miladi": today_str,
            "Tarikh Hijri": hijri_date,
            "Hari": day_name,
            "Imsak": "05:30 AM",
            "Subuh": "05:45 AM",
            "Syuruk": "07:00 AM",
            "Zohor": "01:00 PM",
            "Asar": "04:15 PM",
            "Maghrib": "07:15 PM",
            "Isyak": "08:30 PM"
        }]
    
    def load_prayer_times(self):
        """Load prayer times from CSV file with retry mechanism."""
        data_file_path = self.config_manager.get("data_file_path")
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if os.path.exists(data_file_path):
                    with open(data_file_path, 'r', encoding='utf-8') as file:
                        csv_reader = csv.DictReader(file)
                        self.prayer_times = [row for row in csv_reader]
                    
                    if self.prayer_times:
                        logger.info(f"Prayer times loaded successfully: {len(self.prayer_times)} entries.")
                        return
                    else:
                        logger.warning("Prayer times file exists but contains no data.")
                else:
                    logger.info("No saved prayer times file found.")
                
                # If we reach here, either the file doesn't exist or it's empty
                break
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Error loading prayer times (attempt {retry_count}/{max_retries}): {str(e)}")
                time.sleep(1)  # Wait before retrying
        
        # If we get here, all retries failed or file doesn't exist
        if not self.prayer_times:
            logger.warning("Using fallback prayer times data.")
            self.prayer_times = self.fallback_prayer_times
    
    def save_prayer_times(self, prayer_times=None):
        """Save prayer times to CSV file."""
        if prayer_times is not None:
            self.prayer_times = prayer_times
        
        if not self.prayer_times:
            logger.warning("No prayer times to save.")
            return False
        
        data_file_path = self.config_manager.get("data_file_path")
        backup_path = data_file_path + ".bak"
        
        try:
            # Create a backup of the existing file if it exists
            if os.path.exists(data_file_path):
                try:
                    with open(data_file_path, 'r', encoding='utf-8') as src:
                        with open(backup_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                    logger.info(f"Created backup of prayer times at {backup_path}")
                except Exception as e:
                    logger.warning(f"Failed to create backup: {str(e)}")
            
            # Write the new data
            with open(data_file_path, 'w', newline='', encoding='utf-8') as file:
                fieldnames = [
                    "Tarikh Miladi", "Tarikh Hijri", "Hari",
                    "Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"
                ]
                
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.prayer_times)
            
            logger.info("Prayer times saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to save prayer times: {str(e)}")
            
            # Try to restore from backup if available
            if os.path.exists(backup_path):
                try:
                    with open(backup_path, 'r', encoding='utf-8') as src:
                        with open(data_file_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                    logger.info(f"Restored prayer times from backup after save failure")
                except Exception as restore_error:
                    logger.error(f"Failed to restore from backup: {str(restore_error)}")
            
            return False
    
    def get_prayer_times_for_date(self, date_str):
        """Get prayer times for a specific date with fallback."""
        for entry in self.prayer_times:
            if entry.get("Tarikh Miladi") == date_str:
                return entry
        
        # If not found, check if we need to generate fallback data for this date
        if date_str == datetime.datetime.now().strftime("%d/%m/%Y"):
            logger.warning(f"No prayer times found for today ({date_str}). Using fallback data.")
            return self.fallback_prayer_times[0]
        
        logger.warning(f"No prayer times found for date: {date_str}")
        return None

# Time Utilities
class TimeUtils:
    """Utility class for time-related operations"""
    
    @staticmethod
    def convert_12h_to_24h(time_str):
        """Convert 12-hour time format to 24-hour format."""
        if not time_str:
            return None
            
        try:
            # Try parsing with AM/PM
            time_obj = datetime.datetime.strptime(time_str.strip(), "%I:%M %p")
            return time_obj.strftime("%H:%M")
        except ValueError:
            # Try parsing without AM/PM (assuming it's already 24h)
            try:
                time_obj = datetime.datetime.strptime(time_str.strip(), "%H:%M")
                return time_str.strip()
            except ValueError as e:
                logger.error(f"Error converting time format: {str(e)}, time_str: {time_str}")
                return None
    
    @staticmethod
    def get_malay_date(date=None):
        """Convert date to Malay format."""
        if date is None:
            date = datetime.datetime.now()
            
        # Translate day and month to Malay
        day_translation = {
            "Monday": "Isnin", "Tuesday": "Selasa", "Wednesday": "Rabu",
            "Thursday": "Khamis", "Friday": "Jumaat", "Saturday": "Sabtu", "Sunday": "Ahad"
        }
        month_translation = {
            "January": "Januari", "February": "Februari", "March": "Mac",
            "April": "April", "May": "Mei", "June": "Jun", "July": "Julai",
            "August": "Ogos", "September": "September", "October": "Oktober",
            "November": "November", "December": "Disember"
        }
        
        english_date = date.strftime("%A, %d %B %Y")
        day, rest = english_date.split(", ", 1)
        day_malay = day_translation.get(day, day)
        for eng_month, malay_month in month_translation.items():
            rest = rest.replace(eng_month, malay_month)
        return f"{day_malay}, {rest}"

# Alert Popup
class AlertPopup(QWidget):
    def __init__(self, message, duration=10, parent=None):
        super().__init__(parent)
        self.message = message
        self.duration = duration
        self.time_left = duration
        self.setup_ui()
        
        # Start countdown timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)  # Update every second
        
        # Set window flags for fullscreen popup
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.showFullScreen()
    
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set background color based on alert type
        if "AZAN" in self.message:
            self.setStyleSheet(f"background-color: {UITheme.ALERT_AZAN};")
        elif "IQAMAH" in self.message:
            self.setStyleSheet(f"background-color: {UITheme.ALERT_IQAMAH};")
        else:  # Reminder
            self.setStyleSheet(f"background-color: {UITheme.ALERT_REMINDER};")
        
        # Alert message (large text)
        self.alert_label = QLabel(self.message)
        self.alert_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.alert_label.setStyleSheet("color: white; padding: 20px;")
        self.alert_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.alert_label)
        
        # Countdown timer
        self.countdown_label = QLabel(f"Closing in {self.time_left} seconds")
        self.countdown_label.setFont(QFont("Arial", 24))
        self.countdown_label.setStyleSheet("color: white;")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.countdown_label)
        
        # Close button
        close_button = QPushButton("Close Now")
        close_button.setFont(QFont("Arial", 18))
        close_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        close_button.clicked.connect(self.close)
        close_button.setFixedWidth(200)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def update_countdown(self):
        self.time_left -= 1
        self.countdown_label.setText(f"Closing in {self.time_left} seconds")
        
        if self.time_left <= 0:
            self.timer.stop()
            self.close()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

# Alert Manager
class AlertManager:
    """Manages prayer time alerts and notifications"""
    
    def __init__(self, parent_widget, data_manager):
        self.parent = parent_widget
        self.data_manager = data_manager
        self.current_alert = None
        self.alert_active = False
        self.alert_popup = None
    
    def check_alerts(self, current_datetime):
        """Check and display prayer time alerts."""
        # If no prayer times loaded, skip
        prayer_times = self.data_manager.prayer_times
        if not prayer_times:
            return
        
        # Get today's date in the same format as CSV (DD/MM/YYYY)
        today = current_datetime.strftime("%d/%m/%Y")
        
        # Find today's prayer times
        today_prayers = self.data_manager.get_prayer_times_for_date(today)
        
        if not today_prayers:
            return
        
        # Current time as datetime.time object
        current_time = current_datetime.time()
        
        # Prayer names to check
        prayer_names = ["Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"]
        
        # Check each prayer time for alerts
        for prayer in prayer_names:
            if prayer in today_prayers:
                try:
                    # Convert and parse prayer time string
                    time_24h = TimeUtils.convert_12h_to_24h(today_prayers[prayer])
                    if time_24h:
                        hour, minute = map(int, time_24h.split(':'))
                        prayer_time = datetime.time(hour, minute)
                        prayer_datetime = datetime.datetime.combine(current_datetime.date(), prayer_time)
                        
                        # Calculate time differences
                        diff_seconds = (prayer_datetime - current_datetime).total_seconds()
                        
                        # 10 minutes before prayer time (reminder)
                        if 540 <= diff_seconds <= 600 and not self.alert_active:
                            self.show_alert(f"GET READY FOR {prayer.upper()} PRAYER IN 10 MINUTES", "reminder")
                            self.alert_active = True
                            self.current_alert = prayer
                        
                        # 5 minutes before prayer time
                        elif 270 <= diff_seconds <= 330 and not self.alert_active:
                            self.show_alert(f"{prayer.upper()} PRAYER IN 5 MINUTES", "reminder")
                            self.alert_active = True
                            self.current_alert = prayer
                        
                        # At prayer time (Azan)
                        elif -10 <= diff_seconds <= 10 and not self.alert_active:
                            self.show_alert(f"{prayer.upper()} AZAN IS NOW", "azan")
                            self.alert_active = True
                            self.current_alert = prayer
                        
                        # 10 minutes after prayer time (Iqamah)
                        elif -610 <= diff_seconds <= -590 and not self.alert_active:
                            self.show_alert(f"TIME FOR {prayer.upper()} IQAMAH", "iqamah")
                            self.alert_active = True
                            self.current_alert = prayer
                        
                        # Reset alert state after alert window has passed
                        elif diff_seconds < -610 and self.current_alert == prayer:
                            self.hide_alert()
                
                except (ValueError, AttributeError) as e:
                    logger.error(f"Error processing prayer time alert for {prayer}: {str(e)}")
    
    def show_alert(self, message, alert_type):
        """Show an alert popup with the given message."""
        # Update the marquee text if callback is provided
        if hasattr(self.parent, 'update_marquee_text'):
            self.parent.update_marquee_text(message)
        
        # Set duration based on alert type
        if alert_type == "azan":
            duration = 60 * 3  # 3 minutes for azan alerts
        elif alert_type == "iqamah":
            duration = 60 * 10  # 10 minutes for iqamah alerts
        else:  # reminder
            duration = 30  # 30 seconds for reminders
        
        # Create and show the alert popup
        self.alert_popup = AlertPopup(message, duration, self.parent)
        
        self.alert_active = True
        logger.info(f"Alert shown: {message} ({alert_type})")
    
    def hide_alert(self):
        """Hide the current alert popup."""
        # Close the alert popup if it exists
        if self.alert_popup is not None:
            self.alert_popup.close()
            self.alert_popup = None
        
        self.alert_active = False
        self.current_alert = None
        logger.info("Alert hidden")
    
    def test_alert(self, alert_type="reminder"):
        """Show a test alert."""
        if alert_type == "azan":
            self.show_alert("TEST AZAN ALERT", "azan")
        elif alert_type == "iqamah":
            self.show_alert("TEST IQAMAH ALERT", "iqamah")
        else:
            self.show_alert("TEST REMINDER ALERT", "reminder")

# Marquee Animation Manager
class MarqueeManager:
    """Manages marquee text animations"""
    
    def __init__(self, label):
        self.label = label
        self.original_text = label.text()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_marquee)
    
    def setup_animation(self):
        """Set up the marquee animation."""
        # Stop existing timer if it's running
        if self.timer.isActive():
            self.timer.stop()
        
        # Add padding to create space between repetitions
        padded_text = self.original_text + "     "
        
        # Set the initial text with padding
        self.label.setText(padded_text * 3)  # Repeat the text to ensure continuous scrolling
        
        # Start the timer
        self.timer.start(100)  # Update every 100ms
        logger.debug("Marquee animation setup complete")
    
    def update_marquee(self):
        """Update the marquee text by shifting it one character to the left."""
        current_text = self.label.text()
        # Shift the text one character to the left and append the first character to the end
        new_text = current_text[1:] + current_text[0]
        self.label.setText(new_text)
    
    def update_text(self, message):
        """Update the marquee text with a new message."""
        self.original_text = message
        padded_text = message + "     "
        self.label.setText(padded_text * 3)
        logger.debug(f"Marquee text updated: {message}")
    
    def stop(self):
        """Stop the marquee animation."""
        if self.timer.isActive():
            self.timer.stop()

# UI Builder
class UIBuilder:
    """Responsible for building UI components"""
    
    @staticmethod
    def create_header(mosque_name, settings_callback):
        """Create the header section with mosque info and time display."""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setStyleSheet(f"""
            QFrame#headerFrame {{
                background-color: {UITheme.DARK_BG};
                border-bottom: 2px solid {UITheme.LIGHT_BG};
            }}
        """)
        header_frame.setFixedHeight(120)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Left side - Mosque name and Hijri date
        mosque_info_layout = QVBoxLayout()
        mosque_info_layout.setSpacing(8)
        
        # Mosque name
        mosque_label = QLabel(mosque_name)
        mosque_label.setObjectName("mosqueLabel")
        mosque_label.setFont(QFont("Arial", UITheme.FONT_LARGE, QFont.Weight.Bold))
        mosque_label.setStyleSheet(f"""
            QLabel#mosqueLabel {{  
                color: {UITheme.TEXT_PRIMARY};
                padding-left: 5px;
                border-left: 4px solid {UITheme.PRIMARY_COLOR};
            }}
        """)
        mosque_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        mosque_info_layout.addWidget(mosque_label)
        
        # Hijri date below mosque name
        hijri_label = QLabel("")
        hijri_label.setObjectName("hijriLabel")
        hijri_label.setFont(QFont("Arial", UITheme.FONT_SMALL))
        hijri_label.setStyleSheet(f"""
            QLabel#hijriLabel {{
                color: {UITheme.TEXT_SECONDARY};
                padding-left: 9px;
            }}
        """)
        hijri_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        mosque_info_layout.addWidget(hijri_label)
        
        header_layout.addLayout(mosque_info_layout, 2)
        
        # Add a spacer between left and right sections
        header_layout.addSpacing(20)
        
        # Settings button at top right
        settings_button = QPushButton("")
        settings_button.setObjectName("settingsButton")
        settings_button.setFont(QFont("Arial", 16))
        settings_button.setFixedSize(40, 40)
        settings_button.setStyleSheet(f"""
            QPushButton#settingsButton {{
                background-color: {UITheme.PRIMARY_COLOR};
                color: {UITheme.TEXT_PRIMARY};
                border: none;
                border-radius: 20px;
                padding: 0px;
            }}
            QPushButton#settingsButton:hover {{
                background-color: #2563EB;
            }}
        """)
        settings_button.clicked.connect(settings_callback)
        
        # Right side - Time and date
        time_info_layout = QVBoxLayout()
        time_info_layout.setSpacing(8)
        
        # Current time on top
        time_label = QLabel("")
        time_label.setObjectName("timeLabel")
        time_label.setFont(QFont("Arial", 50, QFont.Weight.Bold))
        time_label.setStyleSheet(f"""
            QLabel#timeLabel {{
                color: {UITheme.TEXT_PRIMARY};
            }}
        """)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_info_layout.addWidget(time_label)
        
        # Malay date below time
        date_label = QLabel("")
        date_label.setObjectName("dateLabel")
        date_label.setFont(QFont("Arial", UITheme.FONT_SMALL))
        date_label.setStyleSheet(f"""
            QLabel#dateLabel {{
                color: {UITheme.TEXT_PRIMARY};
            }}
        """)
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_info_layout.addWidget(date_label)
        
        time_info_layout.setStretch(0, 2)  # Give more space to time
        time_info_layout.setStretch(1, 1)  # Less space for date
        
        # Add to header layout
        header_right_layout = QHBoxLayout()
        header_right_layout.setSpacing(10)
        header_right_layout.addLayout(time_info_layout)
        header_right_layout.addWidget(settings_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        header_layout.addLayout(header_right_layout, 2)
        
        return header_frame, mosque_label, hijri_label, time_label, date_label
    
    @staticmethod
    def create_flash_message_bar(flash_message):
        """Create the flash message bar with marquee animation."""
        flash_container = QFrame()
        flash_container.setObjectName("flashContainer")
        flash_container.setStyleSheet(f"""
            QFrame#flashContainer {{
                background-color: {UITheme.PRIMARY_COLOR};
                border-radius: 0px;
            }}
        """)
        flash_container.setFixedHeight(50)
        flash_layout = QHBoxLayout(flash_container)
        flash_layout.setContentsMargins(10, 5, 10, 5)
        
        # Create a scroll area for the flash message
        scroll_area = QScrollArea()
        scroll_area.setObjectName("flashScrollArea")
        scroll_area.setStyleSheet("""
            QScrollArea#flashScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Flash message label inside a container widget
        flash_content = QWidget()
        flash_content.setStyleSheet("background-color: transparent;")
        flash_content_layout = QHBoxLayout(flash_content)
        flash_content_layout.setContentsMargins(0, 0, 0, 0)
        
        flash_message_label = QLabel(flash_message)
        flash_message_label.setObjectName("flashMessageLabel")
        flash_message_label.setFont(QFont("Arial", UITheme.FONT_SMALL, QFont.Weight.Bold))
        flash_message_label.setStyleSheet(f"""
            QLabel#flashMessageLabel {{
                color: {UITheme.TEXT_PRIMARY};
                background-color: transparent;
            }}
        """)
        flash_message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        flash_content_layout.addWidget(flash_message_label)
        scroll_area.setWidget(flash_content)
        flash_layout.addWidget(scroll_area)
        
        return flash_container, flash_message_label
    
    @staticmethod
    def create_prayer_cards(prayer_names):
        """Create prayer time cards for display."""
        prayer_cards_container = QWidget()
        prayer_cards_container.setObjectName("prayerCardsContainer")
        prayer_cards_container.setStyleSheet(f"""
            QWidget#prayerCardsContainer {{
                background-color: {UITheme.DARK_BG};
            }}
        """)
        prayer_cards_container.setMinimumHeight(200)
        prayer_cards_layout = QHBoxLayout(prayer_cards_container)
        prayer_cards_layout.setContentsMargins(20, 20, 20, 20)
        prayer_cards_layout.setSpacing(15)
        
        prayer_labels = {}
        prayer_times_labels = {}
        
        for prayer in prayer_names:
            card = QFrame()
            card.setObjectName(f"{prayer}Card")
            card.setStyleSheet(f"""
                QFrame#{prayer}Card {{
                    background-color: {UITheme.PRAYER_COLORS.get(prayer, UITheme.LIGHT_BG)};
                    border-radius: {UITheme.BORDER_RADIUS_LARGE}px;
                }}
                QFrame#{prayer}Card:hover {{
                    background-color: #475569;
                }}
            """)
            card_layout = QVBoxLayout(card)
            
            # Prayer name
            name_label = QLabel(prayer)
            name_label.setObjectName(f"{prayer}NameLabel")
            name_label.setFont(QFont("Arial", UITheme.FONT_MEDIUM, QFont.Weight.Bold))
            name_label.setStyleSheet(f"color: {UITheme.TEXT_PRIMARY};")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(name_label)
            prayer_labels[prayer] = name_label
            
            # Prayer time
            time_label = QLabel("--:--")
            time_label.setObjectName(f"{prayer}TimeLabel")
            time_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
            time_label.setStyleSheet(f"color: {UITheme.TEXT_ACCENT};")
            time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(time_label)
            prayer_times_labels[prayer] = time_label
            
            # Add to horizontal layout
            prayer_cards_layout.addWidget(card)
        
        return prayer_cards_container, prayer_labels, prayer_times_labels
    
    @staticmethod
    def create_content_area():
        """Create the main content area."""
        content_area = QWidget()
        content_area.setObjectName("contentArea")
        content_area.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add spacer to push prayer cards to bottom
        content_layout.addStretch(1)
        
        return content_area
    
    @staticmethod
    def create_settings_dialog(config_manager, data_manager, update_callbacks):
        """Create the settings dialog."""
        settings_dialog = QWidget()
        settings_dialog.setWindowTitle("Prayer Times Settings")
        settings_dialog.setMinimumSize(700, 500)
        settings_dialog.setStyleSheet(UITheme.settings_dialog_style())

        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(20)

        # Title
        title_label = QLabel("Prayer Times Settings")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        settings_layout.addWidget(title_label)

        # Mosque name input
        mosque_layout = QHBoxLayout()
        mosque_layout.addWidget(QLabel("Mosque Name:"))
        mosque_input = QLineEdit(config_manager.get("mosque_name", ""))
        mosque_layout.addWidget(mosque_input)
        settings_layout.addLayout(mosque_layout)

        # Add flash message input field
        flash_message_layout = QHBoxLayout()
        flash_message_layout.addWidget(QLabel("Flash Message:"))
        flash_message_input = QLineEdit(config_manager.get("flash_message", ""))
        flash_message_input.setPlaceholderText("Enter flash message here...")
        flash_message_layout.addWidget(flash_message_input)
        settings_layout.addLayout(flash_message_layout)

        # Add button to update the flash message
        update_flash_button = QPushButton("Update Flash Message")
        update_flash_button.setStyleSheet(UITheme.primary_button_style())
        update_flash_button.clicked.connect(lambda: update_callbacks["update_flash"](flash_message_input.text()))
        settings_layout.addWidget(update_flash_button)

        # Add background image button
        bg_button = QPushButton("Add Background Image")
        bg_button.setStyleSheet(UITheme.primary_button_style())
        bg_button.clicked.connect(update_callbacks["browse_bg"])
        settings_layout.addWidget(bg_button)

        # CSV upload button
        csv_button = QPushButton("Upload Prayer Times CSV")
        csv_button.setStyleSheet(UITheme.primary_button_style())
        csv_button.clicked.connect(update_callbacks["upload_csv"])
        settings_layout.addWidget(csv_button)

        # Table to preview uploaded data
        preview_table = QTableWidget(0, 10)
        preview_table.setHorizontalHeaderLabels([
            "Tarikh Miladi", "Tarikh Hijri", "Hari", 
            "Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"
        ])
        preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        settings_layout.addWidget(preview_table)

        # Populate the preview table with current prayer times
        prayer_times = data_manager.prayer_times
        if prayer_times:
            preview_table.setRowCount(len(prayer_times))
            header_labels = [preview_table.horizontalHeaderItem(i).text() for i in range(preview_table.columnCount())]
            for row_idx, row in enumerate(prayer_times):
                for col_idx, col_name in enumerate(header_labels):
                    item = QTableWidgetItem(row.get(col_name, ""))
                    preview_table.setItem(row_idx, col_idx, item)

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.setStyleSheet(UITheme.success_button_style())
        save_button.clicked.connect(lambda: update_callbacks["save_settings"](mosque_input.text(), flash_message_input.text()))
        settings_layout.addWidget(save_button)

        # Add save CSV button
        save_csv_button = QPushButton("Save Prayer Times to CSV")
        save_csv_button.setStyleSheet(UITheme.primary_button_style())
        save_csv_button.clicked.connect(update_callbacks["save_csv"])
        settings_layout.addWidget(save_csv_button)

        # Add test alert buttons
        test_alert_layout = QHBoxLayout()
        
        test_reminder_button = QPushButton("Test Reminder Alert")
        test_reminder_button.setStyleSheet(UITheme.primary_button_style())
        test_reminder_button.clicked.connect(lambda: update_callbacks["test_alert"]("reminder"))
        test_alert_layout.addWidget(test_reminder_button)
        
        test_azan_button = QPushButton("Test Azan Alert")
        test_azan_button.setStyleSheet(UITheme.primary_button_style())
        test_azan_button.clicked.connect(lambda: update_callbacks["test_alert"]("azan"))
        test_alert_layout.addWidget(test_azan_button)
        
        test_iqamah_button = QPushButton("Test Iqamah Alert")
        test_iqamah_button.setStyleSheet(UITheme.primary_button_style())
        test_iqamah_button.clicked.connect(lambda: update_callbacks["test_alert"]("iqamah"))
        test_alert_layout.addWidget(test_iqamah_button)
        
        settings_layout.addLayout(test_alert_layout)

        settings_dialog.setLayout(settings_layout)
        return settings_dialog, preview_table, mosque_input, flash_message_input

# UI Manager
class PrayerTimesUI(QMainWindow):
    def __init__(self, config_manager, data_manager):
        super().__init__()
        
        # Store managers
        self.config_manager = config_manager
        self.data_manager = data_manager
        
        # Initialize app properties
        self.setWindowTitle("Mosque Prayer Times Display")
        self.setMinimumSize(1024, 768)
        
        # App variables
       
        self.prayer_names = ["Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"]
        self.prayer_labels = {}
        self.prayer_times_labels = {}
        self.scroll_timers = []
        
        # Create specialized managers
        self.alert_manager = AlertManager(self, self.data_manager)
        
        # Setup UI components
        self.setup_ui()
        
        # Apply the saved background image if it exists
        background_image_path = self.config_manager.get("background_image_path")
        if background_image_path and os.path.exists(background_image_path):
            self.set_background_image(background_image_path)
        
        # Timer for updating the clock and checking alerts
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every second
        
        # Show the application in fullscreen mode
        self.showFullScreen()
    
    def closeEvent(self, event):
        """Clean up resources when the application is closed."""
        # Stop all timers
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        
        if hasattr(self, 'marquee_manager'):
            self.marquee_manager.stop()
        
        # Stop all scroll timers
        for timer in self.scroll_timers:
            if timer.isActive():
                timer.stop()
        
        # Accept the close event
        event.accept()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()  # Exit the application
    
    def setup_ui(self):
        # Main container with dark background
        container = QWidget()
        container.setObjectName("mainContainer")
        container.setStyleSheet(f"""
            QWidget#mainContainer {{
                background-color: #000000;
            }}
        """)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header section
        header_frame, self.mosque_label, self.hijri_label, self.time_label, self.date_label = UIBuilder.create_header(
            self.config_manager.get("mosque_name", "Mosque Name"),
            self.open_settings
        )
        main_layout.addWidget(header_frame)
        
        # Create flash message bar
        flash_container, self.flash_message_label = UIBuilder.create_flash_message_bar(
            self.config_manager.get("flash_message", "Welcome to the Mosque Prayer Times Display")
        )
        main_layout.addWidget(flash_container)
        
        # Setup marquee animation for flash message
        self.marquee_manager = MarqueeManager(self.flash_message_label)
        self.marquee_manager.setup_animation()
        
        # Create main content area
        self.content_area = UIBuilder.create_content_area()
        main_layout.addWidget(self.content_area, 1)
        
        # Create prayer cards
        prayer_cards_container, self.prayer_labels, self.prayer_times_labels = UIBuilder.create_prayer_cards(self.prayer_names)
        main_layout.addWidget(prayer_cards_container)
        
        # Set central widget
        self.setCentralWidget(container)
        
        # Initialize the clock
        self.update_time()
    
    def open_settings(self):
        """Open the settings dialog and populate it with the current settings."""
        # Check if the settings dialog is already open
        if hasattr(self, 'settings_dialog') and self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return
        
        # Create callbacks dictionary for settings dialog
        update_callbacks = {
            "update_flash": self.update_flash_message,
            "browse_bg": self.browse_background_image,
            "upload_csv": self.upload_csv,
            "save_settings": self.save_settings,
            "save_csv": self.save_csv,
            "test_alert": self.alert_manager.test_alert
        }
        
        # Create settings dialog
        self.settings_dialog, self.preview_table, self.mosque_input, self.flash_message_input = UIBuilder.create_settings_dialog(
            self.config_manager,
            self.data_manager,
            update_callbacks
        )
        
        self.settings_dialog.show()
    
    def upload_csv(self):
        """Upload prayer times from a CSV file and save them locally."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    csv_reader = csv.DictReader(file)
                    prayer_times = []
                    
                    # Clear the preview table
                    self.preview_table.setRowCount(0)
                    
                    # Fill preview table with data
                    for row_idx, row in enumerate(csv_reader):
                        prayer_times.append(row)
                        
                        # Add to preview table
                        self.preview_table.insertRow(row_idx)
                        
                        # Required columns
                        required_columns = [
                            "Tarikh Miladi", "Tarikh Hijri", "Hari", 
                            "Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"
                        ]
                        
                        # Validate columns
                        for col in required_columns:
                            if col not in row:
                                raise KeyError(f"Missing required column: {col}")
                        
                        # Add data to table
                        for col_idx, col_name in enumerate(required_columns):
                            item = QTableWidgetItem(row.get(col_name, ""))
                            self.preview_table.setItem(row_idx, col_idx, item)
                
                # Save the uploaded prayer times
                if self.data_manager.save_prayer_times(prayer_times):
                    QMessageBox.information(self, "Success", f"Successfully loaded and saved {len(prayer_times)} days of prayer times.")
                else:
                    QMessageBox.warning(self, "Warning", "Failed to save prayer times.")
                
            except KeyError as e:
                logger.error(f"CSV format error: {str(e)}")
                QMessageBox.critical(self, "Error", f"CSV format error: {str(e)}")
            except Exception as e:
                logger.error(f"Failed to load CSV: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")
    
    def save_settings(self, mosque_name, flash_message):
        """Save the current settings, including mosque name and prayer times."""
        # Save mosque name
        self.config_manager.set("mosque_name", mosque_name)
        self.mosque_label.setText(mosque_name)
        
        # Save flash message if it was changed
        if flash_message:
            self.config_manager.set("flash_message", flash_message)
            self.update_flash_message(flash_message)
        
        # Update display with today's prayer times
        self.update_prayer_display()
        
        # Close the settings dialog
        self.settings_dialog.close()
        
        QMessageBox.information(self, "Success", "Settings saved successfully.")
    
    def update_time(self):
        """Update the time display and check for prayer time alerts."""
        # Get current time
        current = datetime.datetime.now()
        current_time = current.strftime("%I:%M:%S %p")  # 12-hour format with AM/PM
        
        # Get Malay date
        malay_date = TimeUtils.get_malay_date(current)
        
        # Update time and date displays
        self.time_label.setText(current_time)
        self.date_label.setText(malay_date)
        
        # Update prayer times display
        self.update_prayer_display()
        
        # Check for alerts
        self.alert_manager.check_alerts(current)
    
    def update_prayer_display(self):
        """Update the prayer times display with today's prayer times."""
        # Get prayer times data
        prayer_times = self.data_manager.prayer_times
        if not prayer_times:
            return
        
        # Get today's date in the same format as CSV (DD/MM/YYYY)
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        
        # Find today's prayer times
        today_prayers = self.data_manager.get_prayer_times_for_date(today)
        
        # If found, update the display
        if today_prayers:
            # Update Hijri date
            self.hijri_label.setText(f"{today_prayers['Tarikh Hijri']} H")
            
            # Update prayer times and highlight current prayer
            current_time = datetime.datetime.now().time()
            current_prayer = None
            
            for prayer in self.prayer_names:
                if prayer in today_prayers:
                    # Update display
                    self.prayer_times_labels[prayer].setText(today_prayers[prayer])
                    
                    # Reset styling
                    self.prayer_labels[prayer].setStyleSheet(f"color: {UITheme.TEXT_PRIMARY};")
                    self.prayer_times_labels[prayer].setStyleSheet(f"color: {UITheme.TEXT_ACCENT};")
                    
                    # Check if this is the current prayer
                    try:
                        time_24h = TimeUtils.convert_12h_to_24h(today_prayers[prayer])
                        if time_24h:
                            hour, minute = map(int, time_24h.split(':'))
                            prayer_time = datetime.time(hour, minute)
                            
                            # Highlight the current prayer if the current time is within or past the prayer time
                            if current_time >= prayer_time:
                                current_prayer = prayer
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid prayer time format for {prayer}: {today_prayers[prayer]}")
            
            # Highlight the current prayer
            if current_prayer:
                self.prayer_labels[current_prayer].setStyleSheet(f"color: {UITheme.PRIMARY_COLOR}; font-weight: bold;")
                self.prayer_times_labels[current_prayer].setStyleSheet(f"color: {UITheme.PRIMARY_COLOR}; font-weight: bold;")
    
    def update_flash_message(self, message):
        """Update the flash message in the configuration and display."""
        if message:
            self.config_manager.set("flash_message", message)
            self.marquee_manager.update_text(message)
            if hasattr(self, 'settings_dialog') and self.settings_dialog.isVisible():
                QMessageBox.information(self.settings_dialog, "Success", "Flash message updated successfully.")
            logger.info(f"Flash message updated: {message}")
    
    def browse_background_image(self):
        """Open a file dialog to select a background image and save it to the configuration."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select Background Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            success = self.set_background_image(file_path)
            if success:
                self.config_manager.set("background_image_path", file_path)
                QMessageBox.information(self.settings_dialog, "Success", "Background image applied successfully.")
            else:
                QMessageBox.critical(self.settings_dialog, "Error", "Failed to apply background image.")
    
    def set_background_image(self, image_path):
        """Set a background image for the content area only."""
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"Background image path does not exist: {image_path}")
            return False

        try:
            # Ensure the image path is valid and apply it as a background
            style = f"""
            QWidget#contentArea {{
                background-image: url("{image_path}");
                background-position: center;
                background-repeat: no-repeat;
                background-size: cover;
            }}
            """
            self.content_area.setStyleSheet(style)
            logger.info(f"Background image set: {image_path}")
            return True
        except Exception as e:
            logger.error(f"Error setting background image: {str(e)}")
            return False
    
    def save_csv(self):
        """Save the current prayer times to a CSV file selected by the user."""
        prayer_times = self.data_manager.prayer_times
        if not prayer_times:
            QMessageBox.warning(self.settings_dialog, "Warning", "No prayer times to save.")
            return

        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "Save Prayer Times CSV", "", "CSV Files (*.csv)"
        )

        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    fieldnames = [
                        "Tarikh Miladi", "Tarikh Hijri", "Hari",
                        "Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"
                    ]
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(prayer_times)

                QMessageBox.information(self.settings_dialog, "Success", "Prayer times saved successfully.")
                logger.info(f"Prayer times saved to: {file_path}")
            except Exception as e:
                logger.error(f"Failed to save CSV: {str(e)}")
                QMessageBox.critical(self.settings_dialog, "Error", f"Failed to save CSV: {str(e)}")

# Main application
class PrayerTimesApp:
    def __init__(self):
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        
        # Initialize data manager
        self.data_manager = PrayerTimesDataManager(self.config_manager)
        
        # Initialize UI
        self.ui = PrayerTimesUI(self.config_manager, self.data_manager)
    
    def run(self):
        self.ui.show()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        prayer_times_app = PrayerTimesApp()
        prayer_times_app.run()
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        # Show error message to user
        if QApplication.instance():
            QMessageBox.critical(None, "Critical Error", f"An unexpected error occurred: {str(e)}\n\nPlease check the log file for details.")
        sys.exit(1)
