import sys
import csv
import datetime
import time
import os  # Import the os module
import json  # Import the json module
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QFileDialog, QLineEdit, QFrame,
                            QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTextEdit,
                            QGridLayout, QSpacerItem, QSizePolicy, QScrollArea)
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QRect, QEasingCurve, QSequentialAnimationGroup, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QFontDatabase

class PrayerTimesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize app properties
        self.setWindowTitle("Mosque Prayer Times Display")
        self.setMinimumSize(1024, 768)
        
        # App variables
        self.prayer_times = []
        self.mosque_name = ""
        self.flash_messages = ["", "", ""]
        self.current_alert = None
        self.alert_active = False
        self.next_prayer = None
        self.next_prayer_time = None
        self.marquee_animation = None
        self.config_file_path = "d:/demi-masa-py-1/config.json"  # Path to the configuration file
        self.data_file_path = "d:/demi-masa-py-1/prayer_times.csv"  # Path to the prayer times CSV file
        self.mosque_name_file = "d:/demi-masa-py-1/mosque_name.txt"  # Path to the mosque name file
        self.background_image_path = ""  # Path to the currently applied background image
        self.animations = []  # Store animations to prevent garbage collection
        
        # Load configuration
        self.load_config()
        
        # Load saved prayer times and mosque name
        self.load_prayer_times()
        self.read_mosque_name()
        
        # Prayer labels for the main display
        self.prayer_names = ["Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"]
        self.prayer_labels = {}
        self.prayer_times_labels = {}
        
        # Alert widgets
        self.alert_widget = None
        self.alert_label = None
        
        # Setup UI components
        self.setup_ui()
        
        # Apply the saved background image if it exists
        if self.background_image_path:
            self.set_background_image(self.background_image_path)
        
        # Timer for updating the clock and checking alerts
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every second
        
        # Show the application in fullscreen mode
        self.showFullScreen()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()  # Exit the application
        
    def setup_ui(self):
        # Main container with dark background
        container = QWidget()
        container.setObjectName("mainContainer")  # Assign an object name for styling
        container.setStyleSheet("""
            QWidget#mainContainer {
                background-color: #000000;
            }
        """)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top header section with mosque info on left, time on right
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")  # Assign an object name for styling
        header_frame.setStyleSheet("""
            QFrame#headerFrame {
                background-color: #1E293B;
                border-bottom: 2px solid #334155;
            }
        """)
        header_frame.setFixedHeight(120)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)  # Adjust padding for better alignment
        
        # Left side - Mosque name and Hijri date
        mosque_info_layout = QVBoxLayout()
        mosque_info_layout.setSpacing(8)  # Add spacing between mosque name and Hijri date
        
        # Mosque name
        self.mosque_label = QLabel(self.mosque_name if self.mosque_name else "Mosque Name")
        self.mosque_label.setObjectName("mosqueLabel")  # Assign an object name for styling
        self.mosque_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        self.mosque_label.setStyleSheet("""
            QLabel#mosqueLabel {
                color: white;
                padding-left: 5px;
                border-left: 4px solid #3B82F6;
            }
        """)
        self.mosque_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        mosque_info_layout.addWidget(self.mosque_label)
        
        # Hijri date below mosque name
        self.hijri_label = QLabel("")
        self.hijri_label.setObjectName("hijriLabel")  # Assign an object name for styling
        self.hijri_label.setFont(QFont("Arial", 18))
        self.hijri_label.setStyleSheet("""
            QLabel#hijriLabel {
                color: #94A3B8;
                padding-left: 9px;
            }
        """)
        self.hijri_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        mosque_info_layout.addWidget(self.hijri_label)
        
        header_layout.addLayout(mosque_info_layout, 2)
        
        # Add a spacer between left and right sections
        header_layout.addSpacing(20)
        
        # Settings button at top right
        self.settings_button = QPushButton("")
        self.settings_button.setObjectName("settingsButton")  # Assign an object name for styling
        self.settings_button.setFont(QFont("Arial", 16))
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setStyleSheet("""
            QPushButton#settingsButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 0px;
            }
            QPushButton#settingsButton:hover {
                background-color: #2563EB;
            }
        """)
        self.settings_button.clicked.connect(self.open_settings)
        
        # Right side - Time and date
        time_info_layout = QVBoxLayout()
        time_info_layout.setSpacing(8)  # Add spacing between time and date
        
        # Current time on top
        self.time_label = QLabel("")
        self.time_label.setObjectName("timeLabel")  # Assign an object name for styling
        self.time_label.setFont(QFont("Arial", 50, QFont.Weight.Bold))
        self.time_label.setStyleSheet("""
            QLabel#timeLabel {
                color: white;
            }
        """)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_info_layout.addWidget(self.time_label)
        
        # Malay date below time
        self.date_label = QLabel("")
        self.date_label.setObjectName("dateLabel")  # Assign an object name for styling
        self.date_label.setFont(QFont("Arial", 18))
        self.date_label.setStyleSheet("""
            QLabel#dateLabel {
                color: white;
            }
        """)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_info_layout.addWidget(self.date_label)
        
        time_info_layout.setStretch(0, 2)  # Give more space to time
        time_info_layout.setStretch(1, 1)  # Less space for date
        
        # Add to header layout
        header_right_layout = QHBoxLayout()
        header_right_layout.setSpacing(10)  # Add spacing between time info and settings button
        header_right_layout.addLayout(time_info_layout)
        header_right_layout.addWidget(self.settings_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        header_layout.addLayout(header_right_layout, 2)
        
        main_layout.addWidget(header_frame)
        
        # Add flash message above prayer times
        self.flash_message_label = QLabel("Welcome to the Mosque Prayer Times Display")
        self.flash_message_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.flash_message_label.setStyleSheet("color: white;")
        self.flash_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.add_scrolling_animation(self.flash_message_label)
        main_layout.addWidget(self.flash_message_label)

        # Main content area (for padding and future widgets)
        self.content_area = QWidget()
        self.content_area.setObjectName("contentArea")  # Assign an object name for styling
        self.content_area.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add spacer to push prayer cards to bottom
        content_layout.addStretch(1)
        
        main_layout.addWidget(self.content_area, 1)
        
        # Bottom prayer cards layout (horizontal)
        prayer_cards_container = QWidget()
        prayer_cards_container.setObjectName("prayerCardsContainer")  # Assign an object name for styling
        prayer_cards_container.setStyleSheet("background-color: #1E293B;")
        prayer_cards_container.setMinimumHeight(200)
        prayer_cards_layout = QHBoxLayout(prayer_cards_container)
        prayer_cards_layout.setContentsMargins(20, 20, 20, 20)
        prayer_cards_layout.setSpacing(15)
        
        # Create prayer time cards horizontally
        prayer_colors = {
            "Imsak": "#FF5733",  # Red
            "Subuh": "#33FF57",  # Green
            "Syuruk": "#3357FF",  # Blue
            "Zohor": "#FF33A1",  # Pink
            "Asar": "#FFC300",  # Yellow
            "Maghrib": "#8E44AD",  # Purple
            "Isyak": "#1ABC9C"   # Teal
        }

        for prayer in self.prayer_names:
            card = QFrame()
            card.setObjectName(f"{prayer}Card")  # Assign an object name for styling
            card.setStyleSheet(f"""
                QFrame#{prayer}Card {{
                    background-color: {prayer_colors.get(prayer, "#334155")};
                    border-radius: 10px;
                }}
                QFrame#{prayer}Card:hover {{
                    background-color: #475569;
                }}
            """)
            card_layout = QVBoxLayout(card)
            
            # Prayer name
            name_label = QLabel(prayer)
            name_label.setObjectName(f"{prayer}NameLabel")  # Assign an object name for styling
            name_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
            name_label.setStyleSheet("color: white;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(name_label)
            self.prayer_labels[prayer] = name_label
            
            # Prayer time
            time_label = QLabel("--:--")
            time_label.setObjectName(f"{prayer}TimeLabel")  # Assign an object name for styling
            time_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
            time_label.setStyleSheet("color: #66D2CE;")
            time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(time_label)
            self.prayer_times_labels[prayer] = time_label
            
            # Add to horizontal layout
            prayer_cards_layout.addWidget(card)
        
        main_layout.addWidget(prayer_cards_container)
        
        # Set central widget
        self.setCentralWidget(container)
        
        # Initialize the clock
        self.update_time()
    
    def open_settings(self):
        """
        Open the settings dialog and populate it with the current settings.
        """
        # Check if the settings dialog is already open
        if hasattr(self, 'settings_dialog') and self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return

        # Create settings dialog
        self.settings_dialog = QWidget()
        self.settings_dialog.setWindowTitle("Prayer Times Settings")
        self.settings_dialog.setMinimumSize(700, 500)
        self.settings_dialog.setStyleSheet("""
            QWidget {
                background-color: #1E293B;
                color: white;
            }
            QLabel {
                font-size: 14px;
                margin-bottom: 5px;
            }
            QLineEdit, QTableWidget {
                background-color: #334155;
                color: white;
                border: 1px solid #475569;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #3B82F6;
                color: white;
                padding: 8px;
                border: none;
            }
        """)

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
        self.mosque_input = QLineEdit(self.mosque_name)
        mosque_layout.addWidget(self.mosque_input)
        settings_layout.addLayout(mosque_layout)

        # Add flash message input field
        flash_message_layout = QHBoxLayout()
        flash_message_layout.addWidget(QLabel("Flash Message:"))
        self.flash_message_input = QLineEdit()
        self.flash_message_input.setPlaceholderText("Enter flash message here...")
        flash_message_layout.addWidget(self.flash_message_input)
        settings_layout.addLayout(flash_message_layout)

        # Add button to update the flash message
        update_flash_button = QPushButton("Update Flash Message")
        update_flash_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        update_flash_button.clicked.connect(self.update_flash_message)
        settings_layout.addWidget(update_flash_button)

        # Add background image button
        bg_button = QPushButton("Add Background Image")
        bg_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        bg_button.clicked.connect(self.browse_background_image)
        settings_layout.addWidget(bg_button)

        # CSV upload button
        csv_button = QPushButton("Upload Prayer Times CSV")
        csv_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        csv_button.clicked.connect(self.upload_csv)
        settings_layout.addWidget(csv_button)

        # Table to preview uploaded data
        self.preview_table = QTableWidget(0, 10)
        self.preview_table.setHorizontalHeaderLabels([
            "Tarikh Miladi", "Tarikh Hijri", "Hari", 
            "Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"
        ])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        settings_layout.addWidget(self.preview_table)

        # Populate the preview table with current prayer times
        if self.prayer_times:
            self.preview_table.setRowCount(len(self.prayer_times))
            header_labels = [self.preview_table.horizontalHeaderItem(i).text() for i in range(self.preview_table.columnCount())]
            for row_idx, row in enumerate(self.prayer_times):
                for col_idx, col_name in enumerate(header_labels):
                    item = QTableWidgetItem(row.get(col_name, ""))
                    self.preview_table.setItem(row_idx, col_idx, item)

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        save_button.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_button)

        # Add save CSV button
        save_csv_button = QPushButton("Save Prayer Times to CSV")
        save_csv_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        save_csv_button.clicked.connect(self.save_csv)
        settings_layout.addWidget(save_csv_button)

        self.settings_dialog.setLayout(settings_layout)
        self.settings_dialog.show()
    
    def upload_csv(self):
        """
        Upload prayer times from a CSV file and save them locally.
        """
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    csv_reader = csv.DictReader(file)
                    self.prayer_times = []
                    
                    # Clear the preview table
                    self.preview_table.setRowCount(0)
                    
                    # Fill preview table with data
                    for row_idx, row in enumerate(csv_reader):
                        self.prayer_times.append(row)
                        
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
                            item = QTableWidgetItem(row[col_name])
                            self.preview_table.setItem(row_idx, col_idx, item)
                
                # Save the uploaded prayer times locally
                self.save_prayer_times()
                QMessageBox.information(self, "Success", f"Successfully loaded and saved {len(self.prayer_times)} days of prayer times.")
                
            except KeyError as e:
                QMessageBox.critical(self, "Error", f"CSV format error: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")
    
    def save_settings(self):
        """
        Save the current settings, including mosque name and prayer times.
        """
        # Save mosque name
        self.mosque_name = self.mosque_input.text()
        self.mosque_label.setText(self.mosque_name)
        self.create_mosque_name(self.mosque_name)
        
        # Save prayer times to local storage
        self.save_prayer_times()
        
        # Update display with today's prayer times
        self.update_prayer_display()
        
        # Close the settings dialog
        self.settings_dialog.close()
    
    def update_time(self):
        # Get current time
        current = datetime.datetime.now()
        current_time = current.strftime("%I:%M:%S %p")  # 12-hour format with AM/PM
        
        # Translate day and month to Malay
        day_translation = {
            "Monday": "Isnin", "Tuesday": "Selasa", "Wednesday": "Rabu",
            "Thursday": "Khamis", "Friday": "Jumaat", "Saturday": "Sabtu", "Sunday": "Ahad"
        }
        month_translation = {
            "January": "Januari", "February": "Februari", "March": "Mac", "April": "April",
            "May": "Mei", "June": "Jun", "July": "Julai", "August": "Ogos",
            "September": "September", "October": "Oktober", "November": "November", "December": "Disember"
        }
        
        english_date = current.strftime("%A, %d %B %Y")
        day, rest = english_date.split(", ", 1)
        day_malay = day_translation.get(day, day)
        for eng_month, malay_month in month_translation.items():
            rest = rest.replace(eng_month, malay_month)
        malay_date = f"{day_malay}, {rest}"
        
        # Update time and date displays
        self.time_label.setText(current_time)
        self.date_label.setText(malay_date)
        
        # Update prayer times display
        self.update_prayer_display()
        
        # Check for alerts
        self.check_alerts(current)
    
    def update_prayer_display(self):
        # Find today's prayer times
        if not self.prayer_times:
            return
        
        # Get today's date in the same format as CSV (DD/MM/YYYY)
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        
        # Find today's prayer times
        today_prayers = None
        for entry in self.prayer_times:
            # Check if date matches
            if entry["Tarikh Miladi"] == today:
                today_prayers = entry
                break
        
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
                    self.prayer_labels[prayer].setStyleSheet("color: white;")
                    self.prayer_times_labels[prayer].setStyleSheet("color: #10B981;")
                    
                    # Check if this is the current prayer
                    try:
                        hour, minute = map(int, today_prayers[prayer].split(':'))
                        prayer_time = datetime.time(hour, minute)
                        
                        # Highlight the current prayer if the current time is within or past the prayer time
                        if current_time >= prayer_time:
                            current_prayer = prayer
                    except (ValueError, TypeError):
                        pass
            
            # Highlight the current prayer
            if current_prayer:
                self.prayer_labels[current_prayer].setStyleSheet("color: #3B82F6; font-weight: bold;")
                self.prayer_times_labels[current_prayer].setStyleSheet("color: #3B82F6; font-weight: bold;")

    def check_alerts(self, current):
        # If no prayer times loaded, skip
        if not self.prayer_times:
            return
        
        # Get today's date in the same format as CSV (DD/MM/YYYY)
        today = current.strftime("%d/%m/%Y")
        
        # Find today's prayer times
        today_prayers = None
        for entry in self.prayer_times:
            if entry["Tarikh Miladi"] == today:
                today_prayers = entry
                break
        
        if not today_prayers:
            return
        
        # Current time as datetime.time object
        current_time = current.time()
        
        # Check each prayer time for alerts
        for prayer in self.prayer_names:
            if prayer in today_prayers:
                try:
                    # Parse prayer time string
                    hour, minute = map(int, today_prayers[prayer].split(':'))
                    prayer_time = datetime.time(hour, minute)
                    prayer_datetime = datetime.datetime.combine(current.date(), prayer_time)
                    
                    # Calculate time differences
                    diff_seconds = (prayer_datetime - current).total_seconds()
                    
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
                
                except (ValueError, AttributeError):
                    pass
    
    def show_alert(self, message, alert_type):
        # Update the marquee text with the alert
        self.update_marquee_text(message)
        
        # Set alert styling based on type
        if alert_type == "reminder":
            self.alert_widget.setStyleSheet("background-color: #F59E0B;")  # Amber
        elif alert_type == "azan":
            self.alert_widget.setStyleSheet("background-color: #10B981;")  # Green
        elif alert_type == "iqamah":
            self.alert_widget.setStyleSheet("background-color: #3B82F6;")  # Blue
            
        self.alert_active = True
    
    def hide_alert(self):
        # Reset to normal styling
        self.alert_widget.setStyleSheet("background-color: #4CAF50;")
        
        self.alert_active = False
        self.current_alert = None

    def browse_background_image(self):
        """
        Open a file dialog to select a background image and save it to the configuration.
        """
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select Background Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            self.background_image_path = file_path
            success = self.set_background_image(file_path)
            if success:
                self.save_config()  # Save the background image path to the configuration file
                QMessageBox.information(self, "Success", "Background image applied successfully.")
            else:
                QMessageBox.critical(self, "Error", "Failed to apply background image.")

    def set_background_image(self, image_path):
        """
        Set a background image for the content area only.

        Parameters:
        image_path (str): Path to the image file
        """
        if not image_path or not os.path.exists(image_path):
            return False

        try:
            # Ensure the image path is valid and apply it as a background
            style = f"""
            QWidget#contentArea {{
                background-image: url("{image_path}");
                background-position: center;
                background-repeat: no-repeat;
                background-size: cover;  /* Ensure the image covers the entire area */
            }}
            """
            self.content_area.setStyleSheet(style)  # Apply style to contentArea only
            return True
        except Exception as e:
            print(f"Error setting background image: {str(e)}")
            return False

    def save_csv(self):
        """
        Save the current prayer times to a CSV file in local storage.
        """
        if not self.prayer_times:
            QMessageBox.warning(self, "Warning", "No prayer times to save.")
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
                    writer.writerows(self.prayer_times)

                QMessageBox.information(self, "Success", "Prayer times saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save CSV: {str(e)}")

    def load_prayer_times(self):
        """
        Load prayer times from a local CSV file if it exists.
        """
        if os.path.exists(self.data_file_path):
            try:
                with open(self.data_file_path, 'r', encoding='utf-8') as file:
                    csv_reader = csv.DictReader(file)
                    self.prayer_times = [row for row in csv_reader]
                print("Prayer times loaded successfully.")
            except Exception as e:
                print(f"Error loading prayer times: {str(e)}")
        else:
            print("No saved prayer times found.")

    def save_prayer_times(self):
        """
        Save the current prayer times to a local CSV file.
        """
        if not self.prayer_times:
            QMessageBox.warning(self, "Warning", "No prayer times to save.")
            return

        try:
            with open(self.data_file_path, 'w', newline='', encoding='utf-8') as file:
                fieldnames = [
                    "Tarikh Miladi", "Tarikh Hijri", "Hari",
                    "Imsak", "Subuh", "Syuruk", "Zohor", "Asar", "Maghrib", "Isyak"
                ]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.prayer_times)

            print("Prayer times saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save prayer times: {str(e)}")

    def create_mosque_name(self, name):
        """
        Create or save the mosque name in a text file.
        """
        try:
            with open(self.mosque_name_file, 'w', encoding='utf-8') as file:
                file.write(name)
            self.mosque_name = name
            print("Mosque name saved successfully.")
        except Exception as e:
            print(f"Error saving mosque name: {str(e)}")

    def read_mosque_name(self):
        """
        Read the mosque name from the text file if it exists.
        """
        if os.path.exists(self.mosque_name_file):
            try:
                with open(self.mosque_name_file, 'r', encoding='utf-8') as file:
                    self.mosque_name = file.read().strip()
                print("Mosque name loaded successfully.")
            except Exception as e:
                print(f"Error reading mosque name: {str(e)}")
        else:
            print("No saved mosque name found.")

    def update_mosque_name(self, new_name):
        """
        Update the mosque name in the text file.
        """
        self.create_mosque_name(new_name)

    def delete_mosque_name(self):
        """
        Delete the mosque name file.
        """
        if os.path.exists(self.mosque_name_file):
            try:
                os.remove(self.mosque_name_file)
                self.mosque_name = ""
                print("Mosque name deleted successfully.")
            except Exception as e:
                print(f"Error deleting mosque name: {str(e)}")
        else:
            print("Mosque name file does not exist.")

    def ensure_background_image_folder(self):
        """
        Ensure the background image folder exists.
        """
        if not os.path.exists(self.background_image_folder):
            os.makedirs(self.background_image_folder)
            print(f"Background image folder created at {self.background_image_folder}")

    def create_background_image(self, file_path):
        """
        Save a background image to the folder and set it as the current background.
        """
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Error", "Selected file does not exist.")
            return
        
        try:
            # Copy the image to the background image folder
            file_name = os.path.basename(file_path)
            destination_path = os.path.join(self.background_image_folder, file_name)
            if not os.path.exists(destination_path):
                import shutil
                shutil.copy(file_path, destination_path)
            self.background_image_path = destination_path
            self.set_background_image(self.background_image_path)
            print(f"Background image saved to {destination_path}")
        except Exception as e:
            print(f"Error saving background image: {str(e)}")

    def read_background_image(self):
        """
        Read the current background image from the folder if it exists.
        """
        if self.background_image_path and os.path.exists(self.background_image_path):
            self.set_background_image(self.background_image_path)
            print(f"Background image loaded: {self.background_image_path}")
        else:
            print("No background image set.")

    def update_background_image(self, file_path):
        """
        Update the current background image by replacing it with a new one.
        """
        self.create_background_image(file_path)

    def delete_background_image(self):
        """
        Delete the current background image from the folder.
        """
        if self.background_image_path and os.path.exists(self.background_image_path):
            try:
                os.remove(self.background_image_path)
                self.background_image_path = ""
                self.content_area.setStyleSheet("background-color: #0F172A;")  # Reset to default
                print("Background image deleted successfully.")
            except Exception as e:
                print(f"Error deleting background image: {str(e)}")
        else:
            print("No background image to delete.")

    def load_config(self):
        """
        Load the configuration from the JSON file.
        """
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as file:
                    config = json.load(file)
                    self.background_image_path = config.get("background_image_path", "")
                print("Configuration loaded successfully.")
            except Exception as e:
                print(f"Error loading configuration: {str(e)}")
        else:
            print("No configuration file found.")

    def save_config(self):
        """
        Save the current configuration to the JSON file.
        """
        try:
            config = {
                "background_image_path": self.background_image_path
            }
            with open(self.config_file_path, 'w', encoding='utf-8') as file:
                json.dump(config, file, indent=4)
            print("Configuration saved successfully.")
        except Exception as e:
            print(f"Error saving configuration: {str(e)}")

    def update_flash_message(self):
        """
        Update the flash message with the user input.
        """
        flash_message = self.flash_message_input.text()
        if (flash_message):
            self.flash_message_label.setText(flash_message)
            self.add_scrolling_animation(self.flash_message_label)

    def add_scrolling_animation(self, label):
        """
        Add a scrolling animation to a QLabel using QTimer.

        Parameters:
        label (QLabel): The label to animate.
        """
        # Calculate the width of the label's text
        label_width = label.fontMetrics().boundingRect(label.text()).width()
        label.setFixedWidth(label_width)  # Set the label's width to match the text width

        # Initialize the starting position of the label
        label.move(self.width(), label.y())

        # Create a QTimer to update the label's position
        def update_position():
            current_x = label.x()
            if current_x + label_width < 0:  # Reset position if it goes off-screen
                label.move(self.width(), label.y())
            else:
                label.move(current_x - 2, label.y())  # Move left by 2 pixels

        timer = QTimer(self)
        timer.timeout.connect(update_position)
        timer.start(30)  # Update every 30 milliseconds

        # Store the timer to prevent garbage collection
        self.animations.append(timer)

# Main application
if __name__:
    app = QApplication(sys.argv)
    window = PrayerTimesApp()
    window.show()
    sys.exit(app.exec())