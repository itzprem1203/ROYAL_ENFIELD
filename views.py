import os
import sys
import threading
import time
import requests
from django.core.management import execute_from_command_line
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets
import subprocess
# Global event to signal server to stop
stop_event = threading.Event()

class WebWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("AIR GAUGE LOGICS")
        self.showFullScreen()

        # Create a QWebEngineView widget to display the web page
        self.browser = QtWebEngineWidgets.QWebEngineView(self)

        # Create a layout and add the browser
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.browser)

        # Load the Django server URL
        self.browser.load(QtCore.QUrl("http://127.0.0.1:8000/"))

        # Add a Close button (initially hidden)
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.clicked.connect(self.close)  # Connect to close event
        layout.addWidget(self.close_button)

        # Hide the close button initially
        self.close_button.setVisible(False)

        # Detect URL changes to control visibility of the Close button
        self.browser.urlChanged.connect(self.toggle_close_button)

        # Add a timer to periodically check if the screen is active
        self.inactivity_timer = QtCore.QTimer(self)
        self.inactivity_timer.timeout.connect(self.check_screen_status)
        self.inactivity_timer.start(1000)  # Check every second

        self.screen_on = True  # To track screen status

    def toggle_close_button(self, url):
        """ Show Close button only for the specific URL. """
        if url.toString() == "http://127.0.0.1:8000/":
            self.close_button.setVisible(True)  # Show button for this page
        else:
            self.close_button.setVisible(False)  # Hide button for other pages

    def closeEvent(self, event):
        # Send a POST request to the shutdown endpoint
        try:
            requests.post("http://127.0.0.1:8000/shutdown/")
        except Exception as e:
            print(f"Error sending shutdown request: {e}")
        finally:
            stop_event.set()
            event.accept()

    def check_screen_status(self):
        """ Check if the screen is turned on or off. """
        # Using Qt's screen to detect if the screen is turned off
        screen = QtWidgets.QApplication.primaryScreen()
        geometry = screen.geometry()
        
        # Check if the screen has changed in size (this usually happens when the screen turns on again)
        if geometry.isNull() or geometry.width() == 0 or geometry.height() == 0:
            if self.screen_on:
                self.screen_on = False
                print("Screen turned off.")
                # You can trigger actions here if necessary when the screen is off
        else:
            if not self.screen_on:
                self.screen_on = True
                print("Screen turned on.")
                # Refresh the PyQt window when screen is turned back on
                self.refresh_window()

    def refresh_window(self):
        """ Refresh or reinitialize the window when the screen is turned on again. """
        self.browser.reload()  # Reload the page in the browser view to ensure it resumes correctly.
        self.setWindowState(QtCore.Qt.WindowActive)  # Ensure the window is active and in focus.



def start_web_window():
    app = QtWidgets.QApplication(sys.argv)
    window = WebWindow()
    window.show()
    sys.exit(app.exec_())

def migrate_database():
    # Set the Django settings module environment variable
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_me.settings")
    
    # Run makemigrations
    sys.argv = ["manage.py", "makemigrations"]
    execute_from_command_line(sys.argv)
    
    # Run migrate
    sys.argv = ["manage.py", "migrate"]
    execute_from_command_line(sys.argv)

def start_django_server():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_me.settings")

    # Perform migrations
    migrate_database()

    # Run the Django server as a background process without a visible terminal
    subprocess.Popen(
        ["python", "manage.py", "runserver", "--noreload"],
        stdout=subprocess.DEVNULL,  # Hide output
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,  # Hide terminal on Windows
    )

def wait_for_server():
    url = "http://127.0.0.1:8000/"
    print("Waiting for Django server to start...")
    
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Django server is running.")
                break
        except requests.ConnectionError:
            pass

        time.sleep(1)  # Retry every second



if __name__ == "__main__":
    # Start the Django server in a separate thread
    django_thread = threading.Thread(target=start_django_server)
    django_thread.daemon = True
    django_thread.start()

    # Wait for the Django server to start
    wait_for_server()

    # Start the PyQt5 window after the server starts
    start_web_window()
