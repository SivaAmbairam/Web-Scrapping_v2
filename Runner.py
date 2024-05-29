import sys
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QTextEdit, QLineEdit, QLabel, QCheckBox, QGroupBox, QTabWidget,
    QProgressBar, QDateTimeEdit, QListWidget, QListWidgetItem, QSizePolicy,
    QMessageBox, QTimeEdit
)
from PySide6.QtCore import Qt, Slot, QThread, Signal, QDateTime, QTimer
from PySide6.QtGui import QPixmap, QPalette, QBrush

# Parameters for sizes and colors
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
SCHEDULE_SECTION_MAX_HEIGHT = 40
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 40
DATETIME_MIN_WIDTH = 120
TIME_MIN_WIDTH = 80
PROGRESS_BAR_RANGE = 100

# Colors
BACKGROUND_COLOR = "rgba(39, 228, 245, 50)"
BUTTON_COLOR = "#007BFF"
BUTTON_PRESSED_COLOR = "#0056b3"
BUTTON_DISABLED_BG_COLOR = "#CCCCCC"
BUTTON_DISABLED_TEXT_COLOR = "#666666"
TEXT_COLOR = "white"

# List of Python scripts
script_configuration = {
    'checkbox_scripts': ['Frey_products.py', 'Nasco_Products.py', 'Flinn_products.py', 'VWR_WARDS_Products.py', 'Carolina_Products.py', 'Fisher_Products.py'],  # Scripts to display as checkboxes
    'simultaneous_scripts': ['Frey_products.py', 'Nasco_Products.py', 'Flinn_products.py', 'VWR_WARDS_Products.py', 'Carolina_Products.py', 'Fisher_Products.py'],  # Scripts to run simultaneously
    'end_scripts': ['Nasco_Products.py']  # Scripts to run at the end
}

# Worker thread to run a script and capture output
class ScriptRunner(QThread):
    output_signal = Signal(str)

    def __init__(self, script_name):
        super().__init__()
        self.script_name = script_name
        self.process = None

    def run(self):
        self.process = subprocess.Popen(['python', self.script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True)
        try:
            for line in self.process.stdout:
                self.output_signal.emit(f"{self.script_name}: {line}")

            for line in self.process.stderr:
                self.output_signal.emit(f"{self.script_name}: {line}")
        finally:
            self.process.stdout.close()
            self.process.stderr.close()
            self.process.wait()

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()

class TransparentConsoleTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()

        # Set transparent background
        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")  # Adjust the alpha value for transparency

class ScheduledDateTimeWidget(QWidget):
    removed_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)

        self.label = QLabel()
        self.label.setStyleSheet("padding: 5px;")
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.remove_button = QPushButton("X")
        self.remove_button.setFixedSize(20, 20)
        self.remove_button.setStyleSheet("QPushButton { padding: 0; color: red; }")
        self.remove_button.clicked.connect(self.remove_item)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.remove_button, 0, Qt.AlignRight)
        self.setLayout(self.layout)

    def set_date_time(self, date, time):
        self.label.setText(f"{date.toString('yyyy-MM-dd')}, {time.toString('HH:mm:ss')}")

    def remove_item(self):
        self.removed_signal.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Script Runner with DB Parameters")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)  # Set fixed window size

        # Initialize layout and components
        self.layout = QVBoxLayout()
        self.init_ui()

        # Set background image
        self.bg_image_path = "/Users/g6-media/Documents/BG/5130878.jpg"
        self.set_background_image()

        # Add components to main layout
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.threads = []  # Initialize the threads list

        self.apply_rounded_corners_to_buttons()  # Apply rounded corners to buttons

        # Timer for scheduling tasks
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_scheduled_tasks)
        self.timer.start(60000)  # Check every minute

        self.scheduled_tasks = []

    def set_background_image(self):
        bg_image = QPixmap(self.bg_image_path)
        scaled_bg_image = bg_image.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg_image))
        self.setPalette(palette)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.set_background_image()

    def init_ui(self):
        # DB Configuration GroupBox
        db_group_box = QGroupBox("DB Configuration")
        db_group_layout = QVBoxLayout()

        # Form layout for database parameters
        self.db_username_input = QLineEdit()
        self.db_password_input = QLineEdit()
        self.db_password_input.setEchoMode(QLineEdit.Password)  # Hide password input
        self.db_schema_input = QLineEdit()

        db_form_layout = QHBoxLayout()

        db_form_layout.addWidget(QLabel("DB Username:"))
        db_form_layout.addWidget(self.db_username_input)
        db_form_layout.addWidget(QLabel("DB Password:"))
        db_form_layout.addWidget(self.db_password_input)
        db_form_layout.addWidget(QLabel("DB Schema:"))
        db_form_layout.addWidget(self.db_schema_input)

        db_group_layout.addLayout(db_form_layout)

        # Initialize the database connection status label
        self.db_connection_status_label = QLabel()
        self.db_connection_status_label.setStyleSheet("padding: 5px; color: red;")  # Red color for error messages
        db_group_layout.addWidget(self.db_connection_status_label)

        # Add a button to test the database connection
        self.test_db_connection_button = QPushButton("Test DB Connection")
        self.test_db_connection_button.clicked.connect(self.test_db_connection)
        db_group_layout.addWidget(self.test_db_connection_button)

        db_group_box.setLayout(db_group_layout)
        self.layout.addWidget(db_group_box)

        # GroupBox for checkboxes
        scrape_sites_group_box = QGroupBox("Scrape sites")
        scrape_sites_layout = QVBoxLayout()

        # Checkboxes for selecting scripts
        self.script_checkboxes = []
        for script in script_configuration['checkbox_scripts']:
            checkbox = QCheckBox(script)
            self.script_checkboxes.append(checkbox)
            scrape_sites_layout.addWidget(checkbox)

        scrape_sites_group_box.setLayout(scrape_sites_layout)
        self.layout.addWidget(scrape_sites_group_box)

        # Schedule section
        schedule_group_box = QGroupBox("Schedule")
        schedule_layout = QVBoxLayout()  # Main layout

        # Date and time selection layout
        datetime_layout = QHBoxLayout()

        # DateTimeEdit for selecting schedule date and time
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)  # Enable calendar popup
        self.datetime_edit.setMinimumDateTime(QDateTime.currentDateTime())  # Disable past dates
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd")
        self.datetime_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)  # Adjust size policy
        self.datetime_edit.setMinimumWidth(DATETIME_MIN_WIDTH)  # Adjust minimum width
        datetime_layout.addWidget(self.datetime_edit)

        # Add a QTimeEdit for selecting the time
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QDateTime.currentDateTime().time().addSecs(60))  # Default to 1 minute from now
        self.time_edit.setDisplayFormat("HH:mm:ss")
        self.time_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)  # Adjust size policy
        self.time_edit.setMinimumWidth(TIME_MIN_WIDTH)  # Adjust minimum width
        datetime_layout.addWidget(self.time_edit)

        # Add the datetime_layout to the main layout
        schedule_layout.addLayout(datetime_layout)

        # Schedule button
        self.schedule_button = QPushButton("Schedule")
        self.schedule_button.clicked.connect(self.schedule_scripts)
        schedule_layout.addWidget(self.schedule_button)

        # Sub-section for scheduled dates and times
        self.scheduled_datetimes_list = QListWidget()
        self.scheduled_datetimes_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Adjust size policy
        self.scheduled_datetimes_list.setMinimumHeight(SCHEDULE_SECTION_MAX_HEIGHT)  # Set minimum height
        schedule_layout.addWidget(self.scheduled_datetimes_list)

        schedule_group_box.setLayout(schedule_layout)
        self.layout.addWidget(schedule_group_box)

        # Start and Stop buttons
        self.button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_scripts)
        self.start_button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_scripts)
        self.stop_button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.stop_button.setEnabled(False)

        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.stop_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, PROGRESS_BAR_RANGE)
        self.progress_bar.setValue(0)

        # Console output
        self.tab_widget = QTabWidget()

        # Adding all components to the main layout
        self.layout.addLayout(self.button_layout)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.tab_widget)

    def apply_rounded_corners_to_buttons(self):
        button_style = f"""
                                        QPushButton {{
                                            border-radius: 15px;  /* Adjust the value to control the roundness */
                                            background-color: {BUTTON_COLOR};  /* Background color */
                                            color: {TEXT_COLOR};  /* Text color */
                                            padding: 10px;  /* Padding */
                                        }}
                                        QPushButton:pressed {{
                                            background-color: {BUTTON_PRESSED_COLOR};  /* Darker background when pressed */
                                        }}
                                        QPushButton:disabled {{
                                            background-color: {BUTTON_DISABLED_BG_COLOR};  /* Gray background when disabled */
                                            color: {BUTTON_DISABLED_TEXT_COLOR};  /* Darker text color when disabled */
                                        }}
                                    """
        self.start_button.setStyleSheet(button_style)
        self.stop_button.setStyleSheet(button_style)
        self.schedule_button.setStyleSheet(button_style)

    @Slot()
    def start_scripts(self):
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)

        # Disable checkboxes
        for checkbox in self.script_checkboxes:
            checkbox.setEnabled(False)

        # Clear console tabs
        self.tab_widget.clear()

        # Create and start the ScriptRunner threads
        self.threads = []
        for checkbox, script in zip(self.script_checkboxes, script_configuration['simultaneous_scripts']):
            if checkbox.isChecked():
                console = TransparentConsoleTextEdit()
                console.setReadOnly(True)
                self.tab_widget.addTab(console, script)

                thread = ScriptRunner(script)
                thread.output_signal.connect(console.append)
                self.threads.append(thread)
                thread.start()

    @Slot()
    def stop_scripts(self):
        for thread in self.threads:
            thread.stop()

        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)

        # Re-enable checkboxes
        for checkbox in self.script_checkboxes:
            checkbox.setEnabled(True)

        # Clear console tabs
        self.tab_widget.clear()

        # Reset progress bar
        self.progress_bar.setValue(0)

    @Slot()
    def schedule_scripts(self):
        scheduled_date = self.datetime_edit.date()
        scheduled_time = self.time_edit.time()

        item_widget = ScheduledDateTimeWidget(parent=self.scheduled_datetimes_list)
        item_widget.set_date_time(scheduled_date, scheduled_time)
        item_widget.removed_signal.connect(lambda: self.remove_scheduled_task(item_widget))
        item = QListWidgetItem()
        item.setSizeHint(item_widget.sizeHint())  # Set the size hint to ensure proper display
        self.scheduled_datetimes_list.addItem(item)
        self.scheduled_datetimes_list.setItemWidget(item, item_widget)

        self.scheduled_tasks.append((scheduled_date, scheduled_time, item))

        # Disable schedule button after scheduling
        self.schedule_button.setEnabled(False)

        print(f"Scheduled Date: {scheduled_date.toString('yyyy-MM-dd')}, Time: {scheduled_time.toString('HH:mm:ss')}")

    @Slot()
    def enable_schedule_button(self):
        # Enable schedule button after removing a scheduled task
        self.schedule_button.setEnabled(True)

    def remove_scheduled_task(self, item_widget):
        # Find the item corresponding to the widget
        for i in range(self.scheduled_datetimes_list.count()):
            item = self.scheduled_datetimes_list.item(i)
            if self.scheduled_datetimes_list.itemWidget(item) == item_widget:
                self.scheduled_datetimes_list.takeItem(i)
                self.scheduled_tasks = [(date, time, it) for date, time, it in self.scheduled_tasks if it != item]
                break
        self.enable_schedule_button()

    def check_scheduled_tasks(self):
        current_datetime = QDateTime.currentDateTime()
        for date, time, item in self.scheduled_tasks:
            scheduled_datetime = QDateTime(date, time)
            if current_datetime >= scheduled_datetime:
                self.start_scripts()
                self.scheduled_tasks.remove((date, time, item))

    @Slot()
    def test_db_connection(self):
        # Get the database credentials from the input fields
        username = self.db_username_input.text()
        password = self.db_password_input.text()
        schema = self.db_schema_input.text()
        # Attempt to establish a database connection


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

