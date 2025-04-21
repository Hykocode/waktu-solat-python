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
                            QGridLayout, QSpacerItem, QSizePolicy, QScrollArea,QDialog)
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QRect, QEasingCurve, QSequentialAnimationGroup,QUrl
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QFontDatabase, QPixmap, QPainter, QBrush
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QFileDialog, QLineEdit, QFrame,
                            QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTextEdit,
                            QGridLayout, QSpacerItem, QSizePolicy, QScrollArea, QDialog, QGraphicsOpacityEffect)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


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
    HIGHLIGHT_COLOR = "#48a74c"  # Darker blue
    SUCCESS_COLOR = "#10B981"  # Green
    WARNING_COLOR = "#F59E0B"  # Amber
    DANGER_COLOR = "#EF4444"   # Red
    INFO_COLOR = "#60A5FA"     # Light Blue
    
    DARK_BG = "#1E293B"        # Dark background
    LIGHT_PEACH = "#fff6d2"    # Light peach
    DARKER_BG = "#0F172A"      # Darker background
    LIGHT_BG = "#334155"       # Light background
    
    TEXT_PRIMARY = "#FFFFFF"   # White text
    TEXT_SECONDARY = "#94A3B8" # Gray text
    TEXT_ACCENT = "#FFFFFF"    # white
    
    # Prayer names in Arabic
    PRAYER_NAMES_ARABIC = {
        "Imsak": "إِمْسَاك",
        "Subuh": "صُبْح",
        "Syuruk": "شُرُوق",
        "Zohor": "ظُهْر",
        "Asar": "عَصْر",
        "Maghrib": "مَغْرِب",
        "Isyak": "عِشَاء"
    }

    # Prayer card colors
    PRAYER_COLORS = {
        "Imsak": "#000a8d",   
        "Subuh": "#1355b8",  
        "Syuruk": "#ad1500",  
        "Zohor": "#e4a400",   
        "Asar": "#e43000",    
        "Maghrib": "#a400ad",
        "Isyak": "#3d0255"    
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
    
# Audio Manager
class AudioManager:
    """Manages audio playback for alerts and notifications"""
    
    def __init__(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # Set default volume
        self.audio_output.setVolume(0.7)
        
        # Base directory for sound files
        self.sounds_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "sounds"
        self.sounds_dir.mkdir(exist_ok=True)
        
        # Define sound files
        self.sounds = {
            "reminder_end": str(self.sounds_dir / "reminder_end.mp3"),
            "azan_start": str(self.sounds_dir / "azan_start.mp3"),
            "iqamah_end": str(self.sounds_dir / "iqamah_end.mp3"),
            "notification": str(self.sounds_dir / "notification.mp3")
        }
        
        # Log available sounds
        self._log_available_sounds()
    
    def _log_available_sounds(self):
        """Log which sound files are available"""
        available_sounds = []
        missing_sounds = []
        
        for sound_name, sound_path in self.sounds.items():
            if os.path.exists(sound_path):
                available_sounds.append(sound_name)
            else:
                missing_sounds.append(sound_name)
        
        if available_sounds:
            logger.info(f"Available sounds: {', '.join(available_sounds)}")
        if missing_sounds:
            logger.warning(f"Missing sound files: {', '.join(missing_sounds)}")
    
    def play_sound(self, sound_type):
        """Play a sound by type"""
        if sound_type not in self.sounds:
            logger.warning(f"Unknown sound type: {sound_type}")
            return False
            
        sound_path = self.sounds[sound_type]
        
        if not os.path.exists(sound_path):
            logger.warning(f"Sound file not found: {sound_path}")
            return False
            
        try:
            # Stop any currently playing sound
            self.player.stop()
            
            # Set the new media source and play
            self.player.setSource(QUrl.fromLocalFile(sound_path))
            self.player.play()
            logger.info(f"Playing sound: {sound_type}")
            return True
        except Exception as e:
            logger.error(f"Error playing sound {sound_type}: {str(e)}")
            return False
    
    def stop_sound(self):
        """Stop any currently playing sound"""
        self.player.stop()

# Add this class after the UITheme class
class FontManager:
    """Manages custom fonts for the application"""
    
    MAIN_FONT_ID = None
    ARABIC_FONT_ID = None
    
    @staticmethod
    def load_fonts():
        """Load custom fonts for the application"""
        font_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "fonts"
        font_dir.mkdir(exist_ok=True)
        
        # Load main font
        main_font_path = font_dir / "Outfit-Variable.ttf"  # Change filename to match your font
        if main_font_path.exists():
            FontManager.MAIN_FONT_ID = QFontDatabase.addApplicationFont(str(main_font_path))
            if FontManager.MAIN_FONT_ID != -1:
                logger.info(f"Main font loaded successfully: {QFontDatabase.applicationFontFamilies(FontManager.MAIN_FONT_ID)[0]}")
            else:
                logger.warning("Failed to load main font")
        else:
            logger.warning(f"Main font file not found at {main_font_path}")
        
        # Load Arabic font
        arabic_font_path = font_dir / "CooperArabic.ttf"  # Change filename to match your font
        if arabic_font_path.exists():
            FontManager.ARABIC_FONT_ID = QFontDatabase.addApplicationFont(str(arabic_font_path))
            if FontManager.ARABIC_FONT_ID != -1:
                logger.info(f"Arabic font loaded successfully: {QFontDatabase.applicationFontFamilies(FontManager.ARABIC_FONT_ID)[0]}")
            else:
                logger.warning("Failed to load Arabic font")
        else:
            logger.warning(f"Arabic font file not found at {arabic_font_path}")
    
    @staticmethod
    def get_main_font(size=12, weight=QFont.Weight.Normal):
        """Get the main font with specified size and weight"""
        if FontManager.MAIN_FONT_ID != -1 and FontManager.MAIN_FONT_ID is not None:
            family = QFontDatabase.applicationFontFamilies(FontManager.MAIN_FONT_ID)[0]
            return QFont(family, size, weight)
        return QFont("Arial", size, weight)  # Fallback font
    
    @staticmethod
    def get_arabic_font(size=12, weight=QFont.Weight.Normal):
        """Get the Arabic font with specified size and weight"""
        if FontManager.ARABIC_FONT_ID != -1 and FontManager.ARABIC_FONT_ID is not None:
            family = QFontDatabase.applicationFontFamilies(FontManager.ARABIC_FONT_ID)[0]
            return QFont(family, size, weight)
        return QFont("Arial", size, weight)  # Fallback font

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
        
        # Validate logo_path (path, doesn't need to exist)
        validated["logo_path"] = ConfigValidator.validate_path(
            config.get("logo_path", default_config["logo_path"]),
            "logo_path"
        )
        
        # Validate data_file_path (path, doesn't need to exist)
        validated["data_file_path"] = ConfigValidator.validate_path(
            config.get("data_file_path", default_config["data_file_path"]),
            "data_file_path"
        ) or default_config["data_file_path"]
        
        # Validate background_scaling_mode
        validated["background_scaling_mode"] = config.get("background_scaling_mode", default_config["background_scaling_mode"])
        
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
            "background_scaling_mode": "cover",
            "logo_path": "",  # Add this line for logo path
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
            "Imsak": "N/A",
            "Subuh":"N/A",
            "Syuruk": "N/A",
            "Zohor": "N/A",
            "Asar": "N/A",
            "Maghrib": "N/A",
            "Isyak": "N/A"
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


class IntegratedAlert:
    def __init__(self, parent_ui):
        self.parent = parent_ui
        self.alert_frame = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.remaining_time = 0
        self.countdown_label = None
        self.clock_label = None
        self.update_clock_timer = QTimer()
        self.update_clock_timer.timeout.connect(self.update_clock)
        
        # Initialize alert_type attribute
        self.alert_type = None
          
        # Sound notification thresholds (in seconds)
        self.sound_thresholds = {
            "reminder": 5,  # Play sound when 5 seconds remaining for reminders
            "iqamah": 30,   # Play sound when 30 seconds remaining for iqamah
            "prayer_time": 60  # Play sound when 60 seconds remaining for prayer time
        }
        
        # Track if end sound has been played
        self.end_sound_played = False
        
        # Create audio manager if using audio
        if 'QMediaPlayer' in globals():
            self.audio_manager = AudioManager()
        else:
            self.audio_manager = None

    def format_time(self, seconds):
        """Format seconds into minutes and seconds display"""
        minutes, seconds = divmod(seconds, 60)
        if minutes > 0:
            return f"{minutes} min {seconds} sec"
        else:
            return f"{seconds} seconds"
    
    def show_alert(self, message, duration=10, alert_type="reminder"):
        # Remove existing alert if any
        self.hide_alert()
        
        # Store the alert type
        self.alert_type = alert_type
        
        # Reset end sound flag
        self.end_sound_played = False
        
        # Create alert frame
        self.alert_frame = QFrame(self.parent)
        self.alert_frame.setObjectName("alertFrame")
        
        # Set background color based on alert type
        if alert_type == "prayer_time":
            # Special handling for prayer time alert
            bg_color = "rgba(0, 0, 0, 0.95)"  # Almost black background
            if self.audio_manager: self.audio_manager.play_sound("notification")
            duration = 15 * 60  # 15 minutes
        elif alert_type == "azan":
            bg_color = UITheme.ALERT_AZAN
            if self.audio_manager: self.audio_manager.play_sound("azan_start")
        elif alert_type == "iqamah":
            bg_color = UITheme.ALERT_IQAMAH
            if self.audio_manager: self.audio_manager.play_sound("notification")
        else:
            bg_color = UITheme.ALERT_REMINDER
            if self.audio_manager: self.audio_manager.play_sound("notification")
            
        # Enhanced styling with animation preparation
        self.alert_frame.setStyleSheet(f"""
            QFrame#alertFrame {{
                background-color: {bg_color};
                border: 3px solid white;
                border-radius: 20px;
            }}
        """)
        
        # Layout
        layout = QVBoxLayout(self.alert_frame)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Different layout for prayer time alert
        if alert_type == "prayer_time":
            # Add title at the top
            title_label = QLabel("PRAYER TIME")
            title_label.setFont(FontManager.get_main_font(36, QFont.Weight.Bold))
            title_label.setStyleSheet("color: white; margin-bottom: 20px;")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_label)
            
            # Add prayer name
            prayer_name = message.replace("PRAYER TIME - ", "")
            prayer_label = QLabel(prayer_name)
            prayer_label.setFont(FontManager.get_main_font(28, QFont.Weight.Bold))
            prayer_label.setStyleSheet("color: white; margin-bottom: 30px;")
            prayer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(prayer_label)
            
            # Add digital clock
            self.clock_label = QLabel()
            self.clock_label.setFont(FontManager.get_main_font(72, QFont.Weight.Bold))
            self.clock_label.setStyleSheet("color: white;")
            self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.clock_label)
            
            # Update clock immediately and start timer
            self.update_clock()
            self.update_clock_timer.start(1000)  # Update every second
            
            # Add spacer to push content to center
            layout.addStretch(1)
            
            # Add countdown at the bottom
            formatted_time = self.format_time(duration)
            self.countdown_label = QLabel(f"Closing in {formatted_time}")
            self.countdown_label.setFont(FontManager.get_main_font(18))
            self.countdown_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
            self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.countdown_label)
            
            # Close button
            close_button = QPushButton("Dismiss")
            close_button.setFont(FontManager.get_main_font(16))
            close_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.2);
                    color: white;
                    border: 2px solid white;
                    border-radius: 15px;
                    padding: 10px 20px;
                    margin-top: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.3);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.4);
                }
            """)
            close_button.setFixedWidth(200)
            close_button.setCursor(Qt.CursorShape.PointingHandCursor)
            close_button.clicked.connect(self.hide_alert)
            layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            # Standard alert layout
            layout.addStretch(1)

            # Alert icon based on type
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setFixedHeight(80)
            
            # Set icon based on alert type
            icon_path = ""
            if alert_type == "azan":
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "azan_icon.png")
            elif alert_type == "iqamah":
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "iqamah_icon.png")
            else:
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "reminder_icon.png")
            
            # Try to load the icon
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    icon_label.setPixmap(pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    layout.addWidget(icon_label)
            
            # Alert message with enhanced styling
            alert_label = QLabel(message)
            alert_label.setFont(FontManager.get_main_font(48, QFont.Weight.Bold))
            alert_label.setStyleSheet("color: white; margin: 20px 0;")
            alert_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(alert_label)
            
            # Countdown label with enhanced styling
            formatted_time = self.format_time(duration)
            self.countdown_label = QLabel(f"Closing in {formatted_time}")
            self.countdown_label.setFont(FontManager.get_main_font(24))
            self.countdown_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
            self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.countdown_label)
            
            # Close button with enhanced styling
            close_button = QPushButton("Dismiss")
            close_button.setFont(FontManager.get_main_font(16))
            close_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.2);
                    color: white;
                    border: 2px solid white;
                    border-radius: 15px;
                    padding: 10px 20px;
                    margin-top: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.3);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.4);
                }
            """)
            close_button.setFixedWidth(200)
            close_button.setCursor(Qt.CursorShape.PointingHandCursor)
            close_button.clicked.connect(self.hide_alert)
            layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)
            
            layout.addStretch(1)

        # Position the alert in the center of the parent
        self.alert_frame.setGeometry(0, 0, self.parent.width(), self.parent.height())
        
        # Create opacity effect for animation
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0)
        self.alert_frame.setGraphicsEffect(opacity_effect)
        
        # Show the alert
        self.alert_frame.show()
        
        # Animate the alert appearance
        self.fade_in_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_in_animation.start()
        
        # Start countdown
        self.remaining_time = duration
        self.timer.start(1000)  # Update every second
    
    def update_clock(self):
        """Update the digital clock display"""
        if self.clock_label:
            current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
            self.clock_label.setText(current_time)
    
    def update_countdown(self):
        self.remaining_time -= 1
        if self.countdown_label:
            formatted_time = self.format_time(self.remaining_time)
            self.countdown_label.setText(f"Closing in {formatted_time}")
        
        # Check if we need to play an end sound
        if hasattr(self, 'end_sound_played') and hasattr(self, 'audio_manager') and self.audio_manager:
            if not self.end_sound_played:
                threshold = self.sound_thresholds.get(self.alert_type, 5)
                
                if self.remaining_time <= threshold:
                    self.end_sound_played = True
                    
                    # Play appropriate end sound
                    if self.alert_type == "iqamah":
                        self.audio_manager.play_sound("iqamah_end")
                        logger.info("Playing iqamah end sound")
                    elif self.alert_type == "reminder":
                        self.audio_manager.play_sound("reminder_end")
                        logger.info("Playing reminder end sound")
                    elif self.alert_type == "prayer_time":
                        self.audio_manager.play_sound("reminder_end")
                        logger.info("Playing prayer time end sound")
        
        if self.remaining_time <= 0:
            self.hide_alert()
    
    def hide_alert(self):
        if self.alert_frame:
            self.timer.stop()
            
            # Stop the clock update timer if it's running
            if self.update_clock_timer.isActive():
                self.update_clock_timer.stop()
            
            # Create fade out animation
            opacity_effect = self.alert_frame.graphicsEffect()
            fade_out = QPropertyAnimation(opacity_effect, b"opacity")
            fade_out.setDuration(500)
            fade_out.setStartValue(1)
            fade_out.setEndValue(0)
            fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            # Connect the finished signal to delete the alert frame
            fade_out.finished.connect(lambda: self.delete_alert_frame())
            fade_out.start()
            
            # Stop any playing sounds if audio manager exists
            if hasattr(self, 'audio_manager') and self.audio_manager:
                self.audio_manager.stop_sound()
    
    def delete_alert_frame(self):
        """Delete the alert frame after animation completes"""
        if self.alert_frame:
            self.alert_frame.deleteLater()
            self.alert_frame = None



# Alert Manager
class AlertManager:
    """Manages prayer time alerts and notifications"""
    
    def __init__(self, parent_widget, data_manager):
        self.parent = parent_widget
        self.data_manager = data_manager
        self.current_alert = None
        self.alert_active = False
        self.triggered_alerts = {}  # Stores keys like "Isyak_10min"
        self.integrated_alert = IntegratedAlert(parent_widget)
    
    # Modify the AlertManager.check_alerts method
    def check_alerts(self, current_datetime):
        """Check and display prayer time alerts."""
        prayer_times = self.data_manager.prayer_times
        if not prayer_times:
            return

        # Get today's date in the same format as CSV (DD/MM/YYYY)
        today = current_datetime.strftime("%d/%m/%Y")

        today_prayers = self.data_manager.get_prayer_times_for_date(today)
        if not today_prayers:
            return

        prayer_names = ["Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"]
        azan_prayer_names = ["Subuh", "Zohor", "Asar", "Maghrib", "Isyak"]

        # If an alert is already active, determine if it should be overridden.
        if self.alert_active and self.current_alert:
            parts = self.current_alert.split('_')
            if len(parts) >= 2:
                current_prayer, current_alert_type = parts[0], parts[1]
                # If a higher-priority azan window has arrived (i.e. diff in -30 to 30)
                # then allow overriding the current reminder alert.
                time_str = today_prayers.get(current_prayer, "")
                time_24h = TimeUtils.convert_12h_to_24h(time_str)
                if time_24h:
                    hour, minute = map(int, time_24h.split(':'))
                    prayer_time = datetime.time(hour, minute)
                    prayer_datetime = datetime.datetime.combine(current_datetime.date(), prayer_time)
                    diff_seconds = (prayer_datetime - current_datetime).total_seconds()
                    if -30 <= diff_seconds <= 30 and current_alert_type != "azan":
                        self.hide_alert()
                    else:
                        return  # Otherwise, do not proceed if an alert is active.
            else:
                return

        # Loop through each prayer to determine if an alert should trigger.
        for prayer in prayer_names:
            if prayer in today_prayers:
                try:
                    time_24h = TimeUtils.convert_12h_to_24h(today_prayers[prayer])
                    if not time_24h:
                        continue

                    hour, minute = map(int, time_24h.split(':'))
                    prayer_time = datetime.time(hour, minute)
                    prayer_datetime = datetime.datetime.combine(current_datetime.date(), prayer_time)
                    diff_seconds = (prayer_datetime - current_datetime).total_seconds()

                    # Special handling for Syuruk - only a reminder is needed.
                    if prayer == "Syuruk":
                        if 270 <= diff_seconds <= 330:
                            alert_key = f"{prayer}_5min"
                            if not self.triggered_alerts.get(alert_key):
                                self.triggered_alerts[alert_key] = True
                                self.alert_active = True
                                self.current_alert = alert_key
                                self.show_alert(f"{prayer.upper()} 5 minit lagi", "reminder", duration=28*60)
                            return


                    # Special handling for Imsak - only a reminder is needed.
                    elif prayer == "Imsak":
                        if 270 <= diff_seconds <= 330:
                            self.alert_active = True
                            self.current_alert = f"{prayer}_5min"
                            self.show_alert(f"{prayer.upper()} 5 minit lagi", "reminder")
                            return

                   # For prayers with azan alerts.
                    elif prayer in azan_prayer_names:
                        # 10 minutes before prayer time.
                        if 570 <= diff_seconds <= 630:
                            alert_key = f"{prayer}_10min"
                            if not self.triggered_alerts.get(alert_key):
                                self.triggered_alerts[alert_key] = True
                                self.alert_active = True
                                self.current_alert = alert_key
                                self.show_alert(f"Solat {prayer.upper()} 10 minit lagi", "reminder")
                            return

                        # 5 minutes before prayer time.
                        elif 270 <= diff_seconds <= 330:
                            alert_key = f"{prayer}_5min"
                            if not self.triggered_alerts.get(alert_key):
                                self.triggered_alerts[alert_key] = True
                                self.alert_active = True
                                self.current_alert = alert_key
                                self.show_alert(f"Solat {prayer.upper()} 5 minit lagi", "reminder")
                            return

                        # At prayer time: azan alert.
                        elif -1 <= diff_seconds <= 1:
                            alert_key = f"{prayer}_azan"
                            if not self.triggered_alerts.get(alert_key):
                                self.triggered_alerts[alert_key] = True
                                self.alert_active = True
                                self.current_alert = alert_key
                                self.show_alert(f"Azan {prayer.upper()}", "azan")
                            return

                        # 10 minutes after prayer time: iqamah alert.
                        elif -300 <= diff_seconds <= -240:
                            alert_key = f"{prayer}_iqamah"
                            if not self.triggered_alerts.get(alert_key):
                                self.triggered_alerts[alert_key] = True
                                self.alert_active = True
                                self.current_alert = alert_key
                                self.show_alert("IQAMAH", "iqamah")
                            return
                        elif -1200 <= diff_seconds <= -1140:  # 20 minutes after prayer time (10 min after iqamah)
                            alert_key = f"{prayer}_prayer_time"
                            if not self.triggered_alerts.get(alert_key):
                                self.triggered_alerts[alert_key] = True
                                self.alert_active = True
                                self.current_alert = alert_key
                                self.show_alert(f"PRAYER TIME - {prayer.upper()}", "prayer_time")
                            return

                except (ValueError, AttributeError) as e:
                    logger.error(f"Error processing prayer time alert for {prayer}: {str(e)}")

    
    def show_alert(self, message, alert_type, duration=None):
        """Show an alert with the given message."""
        # Replace prayer names with Arabic versions in the message
        for prayer_name, arabic_name in UITheme.PRAYER_NAMES_ARABIC.items():
            if prayer_name in message:
                message = message.replace(prayer_name, arabic_name)
        # Update the marquee text if callback is provided
        if hasattr(self.parent, 'update_marquee_text'):
            self.parent.update_marquee_text(message)
        
        # Set duration based on alert type if not explicitly provided
        if duration is None:
            if alert_type == "azan":
                duration = 60 * 3  # 3 minutes for azan alerts
            elif alert_type == "iqamah":
                duration = 60 * 10  # 10 minutes for iqamah alerts
            else:  # reminder
                duration = 30  # 30 seconds for reminders
        
        # Show the integrated alert
        self.integrated_alert.show_alert(message, duration, alert_type)
        
        self.alert_active = True
        logger.info(f"Alert shown: {message} ({alert_type}), duration: {duration} seconds")

    
    def hide_alert(self):
        """Hide the current alert."""
        self.integrated_alert.hide_alert()
        self.alert_active = False
        self.current_alert = None
        logger.info("Alert hidden")
    
    def test_alert(self, alert_type="reminder"):
        """Show a test alert."""
        if alert_type == "azan":
            self.show_alert("TEST AZAN ALERT", "azan")
        elif alert_type == "iqamah":
            self.show_alert("TEST IQAMAH ALERT", "iqamah")
        elif alert_type == "prayer_time":
            self.show_alert("PRAYER TIME - TEST", "prayer_time")
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
    
# In UIBuilder.create_header method, add a minimize button next to the settings button:
    @staticmethod
    def create_header(mosque_name, settings_callback):
        """Create the header section with mosque info, logo and time display."""
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
        
        # Left side - Logo and mosque info
        left_layout = QHBoxLayout()
        left_layout.setSpacing(15)  # Space between logo and text
        
        # Logo on the left
        logo_label = QLabel()
        logo_label.setObjectName("logoLabel")
        logo_label.setFixedSize(80, 80)  # Fixed size for the logo
        logo_label.setScaledContents(True)  # Scale the logo to fit the label
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("""
            QLabel#logoLabel {
                background-color: transparent;
            }
        """)
        left_layout.addWidget(logo_label)
        
        # Mosque name and Hijri date on the right of the logo
        mosque_info_layout = QVBoxLayout()
        mosque_info_layout.setSpacing(8)
        
        # Mosque name
        mosque_label = QLabel(mosque_name)
        mosque_label.setObjectName("mosqueLabel")
        mosque_label.setFont(FontManager.get_main_font(UITheme.FONT_LARGE, QFont.Weight.Bold))
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
        hijri_label.setFont(FontManager.get_main_font(UITheme.FONT_SMALL))
        hijri_label.setStyleSheet(f"""
            QLabel#hijriLabel {{
                color: {UITheme.TEXT_SECONDARY};
                padding-left: 9px;
            }}
        """)
        hijri_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        mosque_info_layout.addWidget(hijri_label)
        
        left_layout.addLayout(mosque_info_layout)
        header_layout.addLayout(left_layout, 2)
        
        # Add a spacer between left and right sections
        header_layout.addSpacing(20)
        
        # Right side - Time and date
        time_info_layout = QVBoxLayout()
        time_info_layout.setSpacing(8)
        
        # Current time on top
        time_label = QLabel("")
        time_label.setObjectName("timeLabel")
        time_label.setFont(FontManager.get_main_font(50, QFont.Weight.Bold))
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
        date_label.setFont(FontManager.get_main_font(UITheme.FONT_SMALL))
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
        
        # Add window control buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)
        
        # Settings button
        settings_button = QPushButton("")  # Unicode gear symbol
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
        buttons_layout.addWidget(settings_button)
        
        header_right_layout.addLayout(buttons_layout)
        header_layout.addLayout(header_right_layout, 2)
        
        return header_frame, mosque_label, logo_label, hijri_label, time_label, date_label


    @staticmethod
    def create_settings_dialog(config_manager, data_manager, update_callbacks):
        """Create the settings dialog with organized sections."""
        settings_dialog = QWidget()
        settings_dialog.setWindowTitle("Prayer Times Settings")
        settings_dialog.setMinimumSize(800, 600)
        settings_dialog.setStyleSheet(UITheme.settings_dialog_style())

        # Main layout
        main_layout = QVBoxLayout(settings_dialog)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title_label = QLabel("Prayer Times Settings")
        title_label.setFont(FontManager.get_main_font(24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {UITheme.TEXT_PRIMARY}; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Create a scroll area for the settings content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {UITheme.DARK_BG};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {UITheme.DARKER_BG};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {UITheme.LIGHT_BG};
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        # Container widget for scroll area
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        settings_layout.setSpacing(20)
        
        # ===== SECTION 1: Mosque Information =====
        mosque_group = QFrame()
        mosque_group.setObjectName("settingsSection")
        mosque_group.setStyleSheet(f"""
            QFrame#settingsSection {{
                background-color: {UITheme.LIGHT_BG};
                border-radius: {UITheme.BORDER_RADIUS_LARGE}px;
                padding: 10px;
            }}
        """)
        mosque_layout = QVBoxLayout(mosque_group)
        
        # Section title
        section_title = QLabel("Mosque Information")
        section_title.setFont(FontManager.get_main_font(UITheme.FONT_MEDIUM, QFont.Weight.Bold))
        section_title.setStyleSheet(f"color: {UITheme.TEXT_PRIMARY}; margin-bottom: 10px;")
        mosque_layout.addWidget(section_title)
        
        # Mosque name input
        mosque_name_layout = QHBoxLayout()
        mosque_name_layout.addWidget(QLabel("Mosque Name:"))
        mosque_input = QLineEdit(config_manager.get("mosque_name", ""))
        mosque_input.setPlaceholderText("Enter mosque name...")
        mosque_name_layout.addWidget(mosque_input)
        mosque_layout.addLayout(mosque_name_layout)
        
        # Logo upload
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(QLabel("Mosque Logo:"))
        logo_button = QPushButton("Upload Logo")
        logo_button.setStyleSheet(UITheme.primary_button_style())
        logo_button.clicked.connect(update_callbacks["upload_logo"])
        logo_layout.addWidget(logo_button)
        mosque_layout.addLayout(logo_layout)
        
        settings_layout.addWidget(mosque_group)
        
        # ===== SECTION 2: Display Settings =====
        display_group = QFrame()
        display_group.setObjectName("settingsSection")
        display_group.setStyleSheet(f"""
            QFrame#settingsSection {{
                background-color: {UITheme.LIGHT_BG};
                border-radius: {UITheme.BORDER_RADIUS_LARGE}px;
                padding: 10px;
            }}
        """)
        display_layout = QVBoxLayout(display_group)
        
        # Section title
        display_title = QLabel("Display Settings")
        display_title.setFont(FontManager.get_main_font(UITheme.FONT_MEDIUM, QFont.Weight.Bold))
        display_title.setStyleSheet(f"color: {UITheme.TEXT_PRIMARY}; margin-bottom: 10px;")
        display_layout.addWidget(display_title)
        
        # Flash message
        flash_message_layout = QHBoxLayout()
        flash_message_layout.addWidget(QLabel("Flash Message:"))
        flash_message_input = QLineEdit(config_manager.get("flash_message", ""))
        flash_message_input.setPlaceholderText("Enter flash message here...")
        flash_message_layout.addWidget(flash_message_input)
        display_layout.addLayout(flash_message_layout)
        
        # Update flash message button
        update_flash_button = QPushButton("Update Flash Message")
        update_flash_button.setStyleSheet(UITheme.primary_button_style())
        update_flash_button.clicked.connect(lambda: update_callbacks["update_flash"](flash_message_input.text()))
        display_layout.addWidget(update_flash_button)
        
        # Background image
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background Image:"))
        bg_button = QPushButton("Change Background")
        bg_button.setStyleSheet(UITheme.primary_button_style())
        bg_button.clicked.connect(update_callbacks["browse_bg"])
        bg_layout.addWidget(bg_button)
        display_layout.addLayout(bg_layout)
        
        settings_layout.addWidget(display_group)
        
        # ===== SECTION 3: Prayer Times Data =====
        prayer_data_group = QFrame()
        prayer_data_group.setObjectName("settingsSection")
        prayer_data_group.setStyleSheet(f"""
            QFrame#settingsSection {{
                background-color: {UITheme.LIGHT_BG};
                border-radius: {UITheme.BORDER_RADIUS_LARGE}px;
                padding: 10px;
            }}
        """)
        prayer_data_layout = QVBoxLayout(prayer_data_group)
        
        # Section title
        prayer_data_title = QLabel("Prayer Times Data")
        prayer_data_title.setFont(FontManager.get_main_font(UITheme.FONT_MEDIUM, QFont.Weight.Bold))
        prayer_data_title.setStyleSheet(f"color: {UITheme.TEXT_PRIMARY}; margin-bottom: 10px;")
        prayer_data_layout.addWidget(prayer_data_title)
        
        # CSV upload/download buttons
        csv_buttons_layout = QHBoxLayout()
        
        csv_upload_button = QPushButton("Upload Prayer Times CSV")
        csv_upload_button.setStyleSheet(UITheme.primary_button_style())
        csv_upload_button.clicked.connect(update_callbacks["upload_csv"])
        csv_buttons_layout.addWidget(csv_upload_button)
        
        csv_save_button = QPushButton("Save Prayer Times to CSV")
        csv_save_button.setStyleSheet(UITheme.primary_button_style())
        csv_save_button.clicked.connect(update_callbacks["save_csv"])
        csv_buttons_layout.addWidget(csv_save_button)
        
        prayer_data_layout.addLayout(csv_buttons_layout)
        
        # Table to preview uploaded data
        preview_table = QTableWidget(0, 10)
        preview_table.setHorizontalHeaderLabels([
            "Tarikh Miladi", "Tarikh Hijri", "Hari", 
            "Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"
        ])
        preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        preview_table.setMinimumHeight(200)
        prayer_data_layout.addWidget(preview_table)
        
        # Populate the preview table with current prayer times
        prayer_times = data_manager.prayer_times
        if prayer_times:
            preview_table.setRowCount(len(prayer_times))
            header_labels = [preview_table.horizontalHeaderItem(i).text() for i in range(preview_table.columnCount())]
            for row_idx, row in enumerate(prayer_times):
                for col_idx, col_name in enumerate(header_labels):
                    item = QTableWidgetItem(row.get(col_name, ""))
                    preview_table.setItem(row_idx, col_idx, item)
        
        settings_layout.addWidget(prayer_data_group)
        
        # ===== SECTION 4: Test Alerts =====
        test_group = QFrame()
        test_group.setObjectName("settingsSection")
        test_group.setStyleSheet(f"""
            QFrame#settingsSection {{
                background-color: {UITheme.LIGHT_BG};
                border-radius: {UITheme.BORDER_RADIUS_LARGE}px;
                padding: 10px;
            }}
        """)
        test_layout = QVBoxLayout(test_group)
        
        # Section title
        test_title = QLabel("Test Alerts")
        test_title.setFont(FontManager.get_main_font(UITheme.FONT_MEDIUM, QFont.Weight.Bold))
        test_title.setStyleSheet(f"color: {UITheme.TEXT_PRIMARY}; margin-bottom: 10px;")
        test_layout.addWidget(test_title)
        
       # Test alert buttons
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

        # Add prayer time test button
        test_prayer_time_button = QPushButton("Test Prayer Time Alert")
        test_prayer_time_button.setStyleSheet(UITheme.primary_button_style())
        test_prayer_time_button.clicked.connect(lambda: update_callbacks["test_alert"]("prayer_time"))
        test_alert_layout.addWidget(test_prayer_time_button)

        test_layout.addLayout(test_alert_layout)
        
        settings_layout.addWidget(test_group)
        
        # Add a spacer to push everything up
        settings_layout.addStretch(1)
        
        # Set the container as the scroll area widget
        scroll_area.setWidget(settings_container)
        main_layout.addWidget(scroll_area, 1)  # Give the scroll area most of the space
        
        # ===== Bottom buttons =====
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Add a spacer to push buttons to the right
        buttons_layout.addStretch(1)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(UITheme.danger_button_style())
        cancel_button.clicked.connect(settings_dialog.close)
        buttons_layout.addWidget(cancel_button)
        
        # Save button
        save_button = QPushButton("Save Settings")
        save_button.setStyleSheet(UITheme.success_button_style())
        save_button.clicked.connect(lambda: update_callbacks["save_settings"](mosque_input.text(), flash_message_input.text()))
        buttons_layout.addWidget(save_button)
        
        main_layout.addLayout(buttons_layout)
        
        return settings_dialog, preview_table, mosque_input, flash_message_input

    
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
        flash_message_label.setFont(FontManager.get_main_font(UITheme.FONT_SMALL, QFont.Weight.Bold))
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
        """Create prayer time cards for display in reverse order (right-to-left)."""
        prayer_cards_container = QWidget()
        prayer_cards_container.setObjectName("prayerCardsContainer")
        prayer_cards_container.setStyleSheet(f"""
            QWidget#prayerCardsContainer {{
                background-image: url("images/background.png");
            }}
        """)
        prayer_cards_container.setMinimumHeight(200)
        prayer_cards_layout = QHBoxLayout(prayer_cards_container)
        prayer_cards_layout.setContentsMargins(20, 20, 20, 20)
        prayer_cards_layout.setSpacing(15)
        
        prayer_labels = {}
        prayer_times_labels = {}
        
        # Reverse the prayer names list to display in reverse order
        reversed_prayer_names = list(reversed(prayer_names))
        
        for prayer in reversed_prayer_names:
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
            
            # Only Arabic prayer name (no Malay name)
            arabic_name = UITheme.PRAYER_NAMES_ARABIC.get(prayer, prayer)
            name_label = QLabel(arabic_name)
            name_label.setObjectName(f"{prayer}NameLabel")
            name_label.setFont(FontManager.get_arabic_font(UITheme.FONT_MEDIUM, QFont.Weight.Bold))
            name_label.setStyleSheet(f"color: {UITheme.TEXT_PRIMARY};")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(name_label)
            prayer_labels[prayer] = name_label
            
            # Prayer time
            time_label = QLabel("--:--")
            time_label.setObjectName(f"{prayer}TimeLabel")
            time_label.setFont(FontManager.get_main_font(22, QFont.Weight.Bold))
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
        content_area.setStyleSheet(f"""
            QWidget#contentArea {{
                background-color: {UITheme.DARK_BG};
            }}
        """)
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add spacer to push prayer cards to bottom
        content_layout.addStretch(1)
        
        # Store the original resize event
        content_area._original_resize_event = content_area.resizeEvent
        
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

    # Add logo upload button
    logo_button = QPushButton("Upload Mosque Logo")
    logo_button.setStyleSheet(UITheme.primary_button_style())
    logo_button.clicked.connect(update_callbacks["upload_logo"])
    settings_layout.addWidget(logo_button)

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
        
        # Set window icon - direct file approach
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "app_icon.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning(f"Icon file not found at {icon_path}")
        
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
            scaling_mode = self.config_manager.get("background_scaling_mode", "cover")
            self.set_background_image(background_image_path, scaling_mode)



        
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
        elif event.key() == Qt.Key.Key_F11:
            # Toggle between fullscreen and normal
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()


    
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
        
        # Create header section with logo
        header_frame, self.mosque_label, self.logo_label, self.hijri_label, self.time_label, self.date_label = UIBuilder.create_header(
            self.config_manager.get("mosque_name", "Mosque Name"),
            self.open_settings
        )
        main_layout.addWidget(header_frame)
        
        # Load logo if available
        self.load_logo()
        
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


    def load_logo(self):
        """Load the mosque logo from the configured path"""
        logo_path = self.config_manager.get("logo_path", "")
        if logo_path and os.path.exists(logo_path):
            try:
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # Scale the logo to fit the label while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(
                        80, 80,  # Match the fixed size of the label
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    # Set the pixmap
                    self.logo_label.setPixmap(scaled_pixmap)
                    logger.info(f"Logo loaded successfully from {logo_path}")
                else:
                    logger.warning(f"Failed to load logo from {logo_path}")
            except Exception as e:
                logger.error(f"Error loading logo: {str(e)}")




    
    def minimize_window(self):
        """Minimize the application window."""
        self.showMinimized()
        logger.info("Application window minimized")
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        if self.isFullScreen():
            # Exit fullscreen mode 
            self.showNormal()  # First go to normal mode instead of maximized
            
            # Restore window flags
            self.setWindowFlags(Qt.WindowType.Window)
            self.show()  # Need to call show() after changing window flags
            
            # Then maximize
            self.showMaximized()
            logger.info("Exited fullscreen mode")
            
            # Show a brief notification about keyboard shortcuts
            if hasattr(self, 'marquee_manager'):
                original_text = self.marquee_manager.original_text
                self.marquee_manager.update_text("Exited fullscreen mode. Press F11 to enter fullscreen, ESC to exit.")
                # Restore original text after 5 seconds
                QTimer.singleShot(5000, lambda: self.marquee_manager.update_text(original_text))
        else:
            # Enter true fullscreen mode
            # Hide first to prevent flickering
            self.hide()
            
            # Set window flags to remove title bar, make it stay on top, and bypass window manager
            self.setWindowFlags(
                Qt.WindowType.Window | 
                Qt.WindowType.FramelessWindowHint | 
                Qt.WindowType.WindowStaysOnTopHint | 
                Qt.WindowType.X11BypassWindowManagerHint  # This helps on some Linux systems
            )
            
            # Get the screen geometry
            screen_geometry = QApplication.primaryScreen().geometry()
            
            # Set the window geometry to match the screen
            self.setGeometry(screen_geometry)
            
            # Show and then go fullscreen
            self.show()
            self.showFullScreen()
            
            # Raise to top to ensure it's above everything
            self.raise_()
            self.activateWindow()
            
            logger.info("Entered fullscreen mode")
            
            # Show a brief notification about keyboard shortcuts
            if hasattr(self, 'marquee_manager'):
                original_text = self.marquee_manager.original_text
                self.marquee_manager.update_text("Entered fullscreen mode. Press F11 or ESC to exit.")
                # Restore original text after 5 seconds
                QTimer.singleShot(5000, lambda: self.marquee_manager.update_text(original_text))




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
            "upload_logo": self.upload_logo,  # Add this line
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


    def upload_logo(self):
        """Open a file dialog to select a logo image and save it to the configuration."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select Mosque Logo", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.svg)"
        )
        
        if file_path:
            logger.info(f"Selected logo image: {file_path}")
            
            # Verify the file exists and is readable
            if not os.path.exists(file_path):
                logger.error(f"Selected file does not exist: {file_path}")
                QMessageBox.critical(self.settings_dialog, "Error", "Selected file does not exist.")
                return
                
            if not os.access(file_path, os.R_OK):
                logger.error(f"Selected file is not readable: {file_path}")
                QMessageBox.critical(self.settings_dialog, "Error", "Selected file is not readable.")
                return
            
            # Test loading the image with QPixmap
            test_pixmap = QPixmap(file_path)
            if test_pixmap.isNull():
                logger.error(f"Failed to load logo as pixmap: {file_path}")
                QMessageBox.critical(self.settings_dialog, "Error", 
                                "Failed to load the selected logo. The file may be corrupted or in an unsupported format.")
                return
                
            logger.info(f"Successfully loaded logo: {file_path}, size: {test_pixmap.width()}x{test_pixmap.height()}")
            
            # Save the logo path to configuration
            self.config_manager.set("logo_path", file_path)
            
            # Update the logo display
            self.load_logo()
            
            QMessageBox.information(self.settings_dialog, "Success", "Mosque logo updated successfully.")


    
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
        
        # Make sure logo is preserved (already saved in upload_logo method)
        
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
        if self.alert_manager.alert_active and not self.alert_manager.integrated_alert.alert_frame:
            self.alert_manager.alert_active = False
            self.alert_manager.current_alert = None
        
        # Reset triggered alerts at midnight
        if current.strftime("%H:%M:%S") == "00:00:00":
            self.alert_manager.triggered_alerts.clear()
            logger.info("Reset daily triggered alerts.")

    
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
            next_prayer_time = None
            
            # First pass: find all prayer times and the next prayer
            prayer_time_objects = {}
            for prayer in self.prayer_names:
                if prayer in today_prayers:
                    # Update display
                    self.prayer_times_labels[prayer].setText(today_prayers[prayer])
                    
                    # Reset styling
                    self.prayer_labels[prayer].setStyleSheet(f"color: {UITheme.TEXT_PRIMARY};")
                    self.prayer_times_labels[prayer].setStyleSheet(f"color: {UITheme.TEXT_ACCENT};")
                    
                    # Parse prayer time
                    try:
                        time_24h = TimeUtils.convert_12h_to_24h(today_prayers[prayer])
                        if time_24h:
                            hour, minute = map(int, time_24h.split(':'))
                            prayer_time = datetime.time(hour, minute)
                            prayer_time_objects[prayer] = prayer_time
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid prayer time format for {prayer}: {today_prayers[prayer]}")
            
            # Second pass: determine current prayer
            for i, prayer in enumerate(self.prayer_names):
                if prayer not in prayer_time_objects:
                    continue
                    
                prayer_time = prayer_time_objects[prayer]
                
                # Special handling for Syuruk - only highlight for 30 minutes
                if prayer == "Syuruk":
                    # Calculate minutes since Syuruk
                    now = datetime.datetime.now()
                    syuruk_datetime = datetime.datetime.combine(now.date(), prayer_time)
                    minutes_since_syuruk = (now - syuruk_datetime).total_seconds() / 60
                    
                    # Only highlight Syuruk if we're within 30 minutes after it
                    if current_time >= prayer_time and minutes_since_syuruk <= 28:
                        current_prayer = prayer
                # For other prayers
                elif current_time >= prayer_time:
                    # Check if there's a next prayer and we haven't passed it
                    next_idx = i + 1
                    while next_idx < len(self.prayer_names):
                        next_prayer = self.prayer_names[next_idx]
                        if next_prayer in prayer_time_objects:
                            next_prayer_time = prayer_time_objects[next_prayer]
                            if current_time < next_prayer_time:
                                current_prayer = prayer
                            break
                        next_idx += 1
                    
                    # If we're at the last prayer of the day
                    if next_idx >= len(self.prayer_names):
                        current_prayer = prayer
            
            # Highlight the current prayer
            if current_prayer:
                self.prayer_labels[current_prayer].setStyleSheet(f"color: {UITheme.TEXT_PRIMARY}; font-weight: bold;")
                self.prayer_times_labels[current_prayer].setStyleSheet(f"color: {UITheme.TEXT_PRIMARY}; font-weight: bold;")
                self.prayer_times_labels[current_prayer].setStyleSheet(f"background-color: {UITheme.HIGHLIGHT_COLOR}; color: {UITheme.TEXT_PRIMARY};")

    
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
            logger.info(f"Selected background image: {file_path}")
            
            # Verify the file exists and is readable
            if not os.path.exists(file_path):
                logger.error(f"Selected file does not exist: {file_path}")
                QMessageBox.critical(self.settings_dialog, "Error", "Selected file does not exist.")
                return
                
            if not os.access(file_path, os.R_OK):
                logger.error(f"Selected file is not readable: {file_path}")
                QMessageBox.critical(self.settings_dialog, "Error", "Selected file is not readable.")
                return
            
            # Test loading the image with QPixmap
            test_pixmap = QPixmap(file_path)
            if test_pixmap.isNull():
                logger.error(f"Failed to load image as pixmap: {file_path}")
                QMessageBox.critical(self.settings_dialog, "Error", 
                                "Failed to load the selected image. The file may be corrupted or in an unsupported format.")
                return
                
            logger.info(f"Successfully loaded test pixmap: {file_path}, size: {test_pixmap.width()}x{test_pixmap.height()}")
            
            # Create a dialog to select scaling mode
            scaling_dialog = QDialog(self.settings_dialog)
            scaling_dialog.setWindowTitle("Image Scaling Options")
            scaling_dialog.setMinimumWidth(400)
            scaling_dialog.setStyleSheet(UITheme.settings_dialog_style())
            
            layout = QVBoxLayout(scaling_dialog)
            
            # Add explanation label
            layout.addWidget(QLabel("Select how the background image should be scaled:"))
            
            # Add radio buttons for scaling options
            cover_radio = QPushButton("Cover (Fill while maintaining aspect ratio)")
            cover_radio.setStyleSheet(UITheme.primary_button_style())
            cover_radio.clicked.connect(lambda: apply_scaling("cover"))
            
            contain_radio = QPushButton("Contain (Show entire image)")
            contain_radio.setStyleSheet(UITheme.primary_button_style())
            contain_radio.clicked.connect(lambda: apply_scaling("contain"))
            
            stretch_radio = QPushButton("Stretch (Fill entire area)")
            stretch_radio.setStyleSheet(UITheme.primary_button_style())
            stretch_radio.clicked.connect(lambda: apply_scaling("stretch"))
            
            layout.addWidget(cover_radio)
            layout.addWidget(contain_radio)
            layout.addWidget(stretch_radio)
            
            # Function to apply selected scaling and close dialog
            def apply_scaling(mode):
                try:
                    logger.info(f"Applying background image with scaling mode: {mode}")
                    success = self.set_background_image(file_path, mode)
                    if success:
                        QMessageBox.information(self.settings_dialog, "Success", 
                                            f"Background image applied with {mode} scaling.")
                    else:
                        QMessageBox.critical(self.settings_dialog, "Error", 
                                            "Failed to apply background image.")
                except Exception as e:
                    logger.error(f"Error applying background image: {str(e)}", exc_info=True)
                    QMessageBox.critical(self.settings_dialog, "Error", 
                                        f"Error applying background image: {str(e)}")
                scaling_dialog.accept()
            
            # Show the dialog
            scaling_dialog.exec()


        
    def set_background_image(self, image_path, scaling_mode="cover"):
        """Set a background image for the content area using a QLabel."""
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"Background image path does not exist: {image_path}")
            return False

        try:
            # Import necessary modules
            from PyQt6.QtGui import QPixmap, QPainter
            
            # Store the image path and scaling mode in config
            self.config_manager.set("background_image_path", image_path)
            self.config_manager.set("background_scaling_mode", scaling_mode)
            
            # Create a container widget for the background and content
            container = QWidget()
            container.setObjectName("bgContainer")
            container.setStyleSheet(f"""
                QWidget#bgContainer {{
                    background-color: {UITheme.DARK_BG};
                }}
            """)
            
            # Create a layout for the container
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            # Load the image directly
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                logger.error(f"Failed to load image: {image_path}")
                return False
                
            logger.info(f"Successfully loaded image: {image_path}, size: {pixmap.width()}x{pixmap.height()}")
            
            # Create a background label
            bg_label = QLabel()
            bg_label.setObjectName("bgLabel")
            bg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Set the scaled pixmap
            self._update_background_pixmap(bg_label, pixmap, scaling_mode)
            
            # Add the background label to the container
            container_layout.addWidget(bg_label)
            
            # Position the background label to fill the container
            bg_label.setGeometry(0, 0, container.width(), container.height())
            
            # Create a transparent overlay widget for content
            content_widget = QWidget(container)
            content_widget.setObjectName("contentWidget")
            content_widget.setStyleSheet("background-color: transparent;")
            
            # Create a layout for the content
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(20, 20, 20, 20)
            
            # Transfer all widgets from the old content area
            old_layout = self.content_area.layout()
            if old_layout:
                while old_layout.count():
                    item = old_layout.takeAt(0)
                    if item.widget():
                        content_layout.addWidget(item.widget())
                    elif item.spacerItem():
                        content_layout.addSpacerItem(item.spacerItem())
            
            # Add stretch to push content to bottom
            content_layout.addStretch(1)
            
            # Position the content widget to fill the container
            content_widget.setGeometry(0, 0, container.width(), container.height())
            
            # Replace the content area in the main layout
            main_layout = self.centralWidget().layout()
            for i in range(main_layout.count()):
                if main_layout.itemAt(i).widget() == self.content_area:
                    main_layout.replaceWidget(self.content_area, container)
                    break
            
            # Hide the old content area and show the new one
            self.content_area.hide()
            container.show()
            
            # Update the content_area reference
            self.content_area = container
            
            # Store references to the background label and pixmap
            self.bg_label = bg_label
            self.bg_pixmap = pixmap
            self.bg_scaling_mode = scaling_mode
            
            # Add resize event handler to update the background when resized
            def resize_event(event):
                # Update the background label size
                bg_label.setGeometry(0, 0, container.width(), container.height())
                # Update the content widget size
                content_widget.setGeometry(0, 0, container.width(), container.height())
                # Update the background pixmap scaling
                self._update_background_pixmap(bg_label, self.bg_pixmap, self.bg_scaling_mode)
                # Call the original resize event
                QWidget.resizeEvent(container, event)
            
            container.resizeEvent = resize_event
            
            logger.info(f"Background image set successfully: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting background image: {str(e)}", exc_info=True)
            return False

    def _update_background_pixmap(self, label, pixmap, scaling_mode):
        """Update the background label with a scaled pixmap."""
        try:
            # Get the size of the label
            label_size = label.size()
            if label_size.width() <= 0 or label_size.height() <= 0:
                # If the label doesn't have a valid size yet, use the content area size
                label_size = self.content_area.size()
            
            # Scale the pixmap based on the scaling mode
            if scaling_mode == "contain":
                scaled_pixmap = pixmap.scaled(
                    label_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            elif scaling_mode == "stretch":
                scaled_pixmap = pixmap.scaled(
                    label_size,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:  # Default to "cover"
                scaled_pixmap = pixmap.scaled(
                    label_size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # If the scaled pixmap is larger than the label, crop it to center
                if scaled_pixmap.width() > label_size.width() or scaled_pixmap.height() > label_size.height():
                    # Create a new pixmap of the label size
                    cropped_pixmap = QPixmap(label_size)
                    cropped_pixmap.fill(Qt.GlobalColor.transparent)
                    
                    # Calculate the position to center the scaled pixmap
                    x = max(0, (scaled_pixmap.width() - label_size.width()) // 2)
                    y = max(0, (scaled_pixmap.height() - label_size.height()) // 2)
                    
                    # Draw the scaled pixmap onto the cropped pixmap
                    painter = QPainter(cropped_pixmap)
                    painter.drawPixmap(
                        0, 0, label_size.width(), label_size.height(),
                        scaled_pixmap, x, y, label_size.width(), label_size.height()
                    )
                    painter.end()
                    
                    scaled_pixmap = cropped_pixmap
            
            # Set the scaled pixmap on the label
            label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            logger.error(f"Error updating background pixmap: {str(e)}", exc_info=True)
   
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
    
    
    def test_prayer_alert(self, prayer_name):
        """Test alert for a specific prayer time"""
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        today_prayers = self.data_manager.get_prayer_times_for_date(today)
        
        if today_prayers and prayer_name in today_prayers:
            self.alert_manager.show_alert(f"{prayer_name.upper()} AZAN IS NOW", "azan")
            return True
        return False

# Main application
class PrayerTimesApp:
    def __init__(self):

        
        # Load custom fonts
        FontManager.load_fonts()

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
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "app_icon.svg")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        prayer_times_app = PrayerTimesApp()
        prayer_times_app.run()
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        # Show error message to user
        if QApplication.instance():
            QMessageBox.critical(None, "Critical Error", f"An unexpected error occurred: {str(e)}\n\nPlease check the log file for details.")
        sys.exit(1)

