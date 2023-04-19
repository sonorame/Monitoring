#в доработку
from datetime import datetime
import os
import sys
import zipfile
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal
import smtplib
import psycopg2
import configparser
import logging

log_file = os.path.join(os.path.dirname(__file__), "setup.log")
logging.basicConfig(filename=log_file, level=logging.DEBUG)

class ConnectThread(QThread):
    connect_signal = pyqtSignal(bool)

    def __init__(self, host, port, username, password, database=None):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database

    def run(self):
        try:
            if self.database is None:
                # Connect to SMTP server using the provided data
                server = smtplib.SMTP(self.host, self.port)
                server.starttls()
                server.login(self.username, self.password)
                server.quit()
            else:
                # Connect to PostgreSQL database using the provided data
                conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.username,
                    password=self.password,
                    database=self.database
                )
                conn.close()
            # If connection is successful, emit signal with True
            self.connect_signal.emit(True)
        except Exception as e:
            # If connection fails, emit signal with False
            self.connect_signal.emit(False)
            logging.error(f"time: {datetime.now()} Error in (ConnectThread) class method (run): {e}")

class UnpackThread(QThread):
    progress_signal = pyqtSignal(int)
    unpack_signal = pyqtSignal(str)

    def __init__(self, zip_path, extract_path):
        super().__init__()
        self.zip_path = zip_path
        self.extract_path = extract_path
    try:
        def run(self):
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                total_files = len(zip_ref.infolist())
                for i, file in enumerate(zip_ref.infolist()):
                    zip_ref.extract(file, self.extract_path)
                    progress = int((i+1) / total_files * 100)
                    self.progress_signal.emit(progress)
            self.unpack_signal.emit(self.extract_path)
    except Exception as e:
        logging.error(f"time: {datetime.now()} Error in (UnpackThread) class method (run): {e}")


class SetupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Setup check SMTP')
        self.setFixedSize(400, 300)

        # SMTP connection fields
        self.host_label = QLabel('SMTP Host:', self)
        self.host_label.move(50, 50)
        self.host_edit = QLineEdit(self)
        self.host_edit.move(150, 50)
        self.port_label = QLabel('SMTP Port:', self)
        self.port_label.move(50, 80)
        self.port_edit = QLineEdit(self)
        self.port_edit.move(150, 80)
        self.username_label = QLabel('Username:', self)
        self.username_label.move(50, 110)
        self.username_edit = QLineEdit(self)
        self.username_edit.move(150, 110)
        self.password_label = QLabel('Password:', self)
        self.password_label.move(50, 140)
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.move(150, 140)

        # Check connection button
        self.check_button = QPushButton('Check Connection', self)
        self.check_button.move(50, 200)
        self.check_button.clicked.connect(self.connect)     

        # Next button
        self.install_button = QPushButton('Next', self)
        self.install_button.move(150, 200)
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self.open_new_window)

    def connect(self):
        host = self.host_edit.text()
        port = self.port_edit.text()
        username = self.username_edit.text()
        password = self.password_edit.text()

        # Start connection thread
        self.connect_thread = ConnectThread(host, port, username, password)
        self.connect_thread.connect_signal.connect(self.connection_result)
        self.connect_thread.start()

    def connection_result(self, success):
        if success:
            self.install_button.setEnabled(True)
            QMessageBox.information(self, 'Connection', 'Connection successful!')
        else:
            QMessageBox.warning(self, 'Connection', 'Connection failed!')

    def open_new_window(self):
        self.new_window = NewWindow()
        self.new_window.show()
        self.close()

class NewWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Setup check DB')
        self.setFixedSize(400, 300)

        # Database connection fields
        self.host_label = QLabel('Database Host:', self)
        self.host_label.move(50, 50)
        self.host_edit = QLineEdit(self)
        self.host_edit.move(150, 50)
        self.port_label = QLabel('Database Port:', self)
        self.port_label.move(50, 80)
        self.port_edit = QLineEdit(self)
        self.port_edit.move(150, 80)
        self.username_label = QLabel('Username:', self)
        self.username_label.move(50, 110)
        self.username_edit = QLineEdit(self)
        self.username_edit.move(150, 110)
        self.password_label = QLabel('Password:', self)
        self.password_label.move(50, 140)
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.move(150, 140)
        self.database_label = QLabel('Database name:', self)
        self.database_label.move(50, 170)
        self.database_edit = QLineEdit(self)
        self.database_edit.move(150, 170)

        # Check connection button
        self.check_button = QPushButton('Check Connection', self)
        self.check_button.move(50, 200)
        self.check_button.clicked.connect(self.connect)

        # Install button
        self.install_button = QPushButton('Install', self)
        self.install_button.move(150, 200)
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self.install)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 250, 300, 20)
        self.progress_bar.setVisible(False)

    def connect(self):
        host = self.host_edit.text()
        port = self.port_edit.text()
        username = self.username_edit.text()
        password = self.password_edit.text()
        database = self.database_edit.text()

        # Start connection thread
        self.connect_thread = ConnectThread(host, port, username, password, database)
        self.connect_thread.connect_signal.connect(self.connection_result)
        self.connect_thread.start()

    def connection_result(self, success):
        if success:
            self.install_button.setEnabled(True)
            QMessageBox.information(self, 'Connection', 'Connection successful!')
        else:
            QMessageBox.warning(self, 'Connection', 'Connection failed!')


    def install(self):
        try:
            zip_path = os.path.join(os.path.dirname(__file__), 'monitoring.zip')
            if not zip_path:
                return

            extract_path = QFileDialog.getExistingDirectory(self, 'Select Extract Path')
            if not extract_path:
                return
            # Start unpacking thread
            self.install_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.unpack_thread = UnpackThread(zip_path, extract_path)
            self.unpack_thread.progress_signal.connect(self.progress_bar.setValue)
            self.unpack_thread.unpack_signal.connect(lambda: self.update_config(extract_path))
            self.unpack_thread.finished.connect(self.close)
            self.unpack_thread.start()
        except Exception as e:
            logging.error(f"time: {datetime.now()} Error in (NewWindow) class method (install): {e}")

    def update_config(self, extract_path):
        config_path = os.path.join(extract_path, 'monitoring/monitoring.config')
        config = configparser.ConfigParser()
        config.read(config_path)
        try:
            # Update SMTP settings
            config['smtp']['server'] = self.host_edit.text()
            config['smtp']['port'] = self.port_edit.text()
            config['smtp']['username'] = self.username_edit.text()
            config['smtp']['password'] = self.password_edit.text()

            # Update database settings (if applicable)
            if self.database_edit is not None:
                config['database']['host'] = self.host_edit.text()
                config['database']['port'] = self.port_edit.text()
                config['database']['user'] = self.username_edit.text()
                config['database']['password'] = self.password_edit.text()
                config['database']['name'] = self.database_edit.text()

            # Write changes to file
            with open(config_path, 'w') as config_file:
                config.write(config_file)
        except Exception as e:
            logging.error(f"time: {datetime.now()} Error in (NewWindow) class method (update_config): {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dataBasewindow = NewWindow()
    mainwindow = SetupWindow()
    mainwindow.show()
    sys.exit(app.exec_())