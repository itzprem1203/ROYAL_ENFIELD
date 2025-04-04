import os
import sys
import threading
import time
import requests
from django.core.management import execute_from_command_line
from PyQt6 import QtWidgets, QtCore, QtWebEngineWidgets
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction

# Global event to stop the server
stop_event = threading.Event()

class WebWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("AIR GAUGE LOGICS")
        self.showFullScreen()

        # Create QWebEngineView
        self.browser = QtWebEngineWidgets.QWebEngineView(self)
        self.setCentralWidget(self.browser)

        # Load Django server URL
        self.browser.setUrl(QUrl("http://127.0.0.1:8000/"))

        # Close button (Initially hidden)
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.clicked.connect(self.close)
        self.close_button.setVisible(False)

        # Detect URL changes for Close button visibility
        self.browser.urlChanged.connect(self.toggle_close_button)

        # Timer for screen status check
        self.inactivity_timer = QtCore.QTimer(self)
        self.inactivity_timer.timeout.connect(self.check_screen_status)
        self.inactivity_timer.start(1000)  # Check every second

        self.screen_on = True  

    def toggle_close_button(self, url):
        """ Show Close button only for the homepage. """
        if url.toString() == "http://127.0.0.1:8000/":
            self.close_button.setVisible(True)
        else:
            self.close_button.setVisible(False)

    def closeEvent(self, event):
        """ Stop Django server on close. """
        try:
            requests.post("http://127.0.0.1:8000/shutdown/")
        except Exception as e:
            print(f"Error stopping server: {e}")
        finally:
            stop_event.set()
            event.accept()

    def check_screen_status(self):
        """ Detect screen power state. """
        screen = QtWidgets.QApplication.primaryScreen()
        geometry = screen.geometry()

        if geometry.isNull() or geometry.width() == 0 or geometry.height() == 0:
            if self.screen_on:
                self.screen_on = False
                print("Screen turned off.")
        else:
            if not self.screen_on:
                self.screen_on = True
                print("Screen turned on.")
                self.refresh_window()

    def refresh_window(self):
        """ Reload the page when screen wakes up. """
        self.browser.reload()
        self.setWindowState(QtCore.Qt.WindowState.WindowActive)

def start_web_window():
    """ Start the PyQt6 WebEngine window. """
    app = QtWidgets.QApplication(sys.argv)
    window = WebWindow()
    window.show()
    sys.exit(app.exec())

def migrate_database():
    """ Perform Django migrations before running the server. """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_me.settings")
    sys.argv = ["manage.py", "makemigrations"]
    execute_from_command_line(sys.argv)
    sys.argv = ["manage.py", "migrate"]
    execute_from_command_line(sys.argv)

def start_django_server():
    """ Run the Django server with migrations. """
    migrate_database()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_me.settings")
    sys.argv = ["manage.py", "runserver", "--noreload"]
    while not stop_event.is_set():
        try:
            execute_from_command_line(sys.argv)
        except SystemExit:
            break  # Stop when the event is triggered

def wait_for_server():
    """ Wait for Django server to be available. """
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
        time.sleep(1)

if __name__ == "__main__":
    django_thread = threading.Thread(target=start_django_server, daemon=True)
    django_thread.start()

    wait_for_server()

    start_web_window()


























# #!/usr/bin/env python
# """Django's command-line utility for administrative tasks."""
# import os
# import sys


# def main():
#     """Run administrative tasks."""
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_me.settings')
#     try:
#         from django.core.management import execute_from_command_line
#     except ImportError as exc:
#         raise ImportError(
#             "Couldn't import Django. Are you sure it's installed and "
#             "available on your PYTHONPATH environment variable? Did you "
#             "forget to activate a virtual environment?"
#         ) from exc
#     execute_from_command_line(sys.argv)


# if __name__ == '__main__':
#     main()
