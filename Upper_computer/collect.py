import sys
import os
import re
import time
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QComboBox, QLabel, QLineEdit, \
    QMessageBox, QFileDialog, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPalette, QColor

# Constants
DEF_TIME_FOR_NOW = time.localtime()
DEF_TIME_MONTH = str(DEF_TIME_FOR_NOW.tm_mon)
DEF_TIME_DAY = str(DEF_TIME_FOR_NOW.tm_mday)
DEF_FILE_NAME_SEPERATOR = '_'
DEF_FILE_FORMAT = '.txt'
DEF_TITLE_STRING = 'IMU\n'
DEF_BAUD_RATE = 921600

motion_name = ['RightAngle', 'SharpAngle', 'Lightning', 'Triangle', 'Letter_h', 'letter_R', 'letter_W', 'letter_phi',
               'Circle', 'UpAndDown', 'Horn', 'Wave', 'NoMotion']


class SerialThread(QThread):
    received_data = pyqtSignal(str)     # 定义一个信号
    finished = pyqtSignal()

    def __init__(self, port, baud_rate): # 需要传递的参数：端口 && 波特率
        super().__init__()  # 继承父类 QThread 的构造函数
        self.port = port
        self.baud_rate = baud_rate
        self.running = True

    def run(self):
        with serial.Serial(port=self.port,
                           baudrate=self.baud_rate,
                           bytesize=serial.EIGHTBITS,
                           parity=serial.PARITY_NONE,
                           stopbits=serial.STOPBITS_ONE,
                           timeout=0.5) as ser:
            while self.running:
                received = ser.readall().decode("ASCII") # 数据 原使用：readall()
                # 串口接受到新数据，发射信号 并传递数据
                if received:
                    print(f"Received data: {received}")
                    self.received_data.emit(received)
        self.finished.emit()

    def stop(self):
        self.running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.serial_thread = None
        self.save_path = './TraningData' + DEF_FILE_NAME_SEPERATOR + DEF_TIME_MONTH + DEF_FILE_NAME_SEPERATOR + DEF_TIME_DAY + '/'
        self.setup_ui() # 析构函数里执行的函数

    def setup_ui(self):
        self.setWindowTitle("Serial Communication")
        self.setGeometry(100, 100, 400, 400)

        # Set background color and font color for the entire window
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(50, 50, 50))  # Dark background
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # White text
        self.setPalette(palette)

        # Styling the widgets
        style_sheet = """
            QLabel, QComboBox, QLineEdit, QPushButton {
                color: white;               /* Text color */
                background-color: #2E2E2E;  /* Background for combo box, buttons */
                border: 1px solid #FFFFFF;  /* White border */
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5E5E5E;  /* Button hover effect */
            }
        """
        self.setStyleSheet(style_sheet)

        central_widget = QWidget()
        layout = QVBoxLayout()

        # ------创建布局-----
        self.port_combo = QComboBox()
        self.port_combo.addItems(self.get_ports())
        layout.addWidget(QLabel("Select Serial Port:"))
        layout.addWidget(self.port_combo)

        self.motion_combo = QComboBox()
        self.motion_combo.addItems(motion_name)
        layout.addWidget(QLabel("Select Motion:"))
        layout.addWidget(self.motion_combo)

        self.record_count_input = QLineEdit()
        self.record_count_input.setPlaceholderText("Enter number of records")
        layout.addWidget(QLabel("Number of Records:"))
        layout.addWidget(self.record_count_input)

        self.select_path_button = QPushButton("Select Save Path")
        self.select_path_button.clicked.connect(self.select_save_path)
        layout.addWidget(self.select_path_button)

        self.start_button = QPushButton("Start Recording")
        self.start_button.clicked.connect(self.start_recording) # start record!!
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Recording")
        self.stop_button.clicked.connect(self.stop_recording)   # stop!!
        layout.addWidget(self.stop_button)

        self.status_label = QLabel("Status: Idle")
        layout.addWidget(self.status_label)

        # 将控件添加到布局中
        self.setCentralWidget(central_widget) #？？？
        central_widget.setLayout(layout)
        # ------------------

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_data)

    def get_ports(self):
        port_list = list(serial.tools.list_ports.comports())
        return [port.device for port in port_list]

    def select_save_path(self): # 选择文件
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory", self.save_path)
        if directory:
            self.save_path = directory
            self.status_label.setText(f"Save path selected: {self.save_path}")

    def start_recording(self):
        if self.serial_thread is not None and self.serial_thread.isRunning():
            QMessageBox.warning(self, "Recording Error", "Recording is already in progress.")
            return

        port = self.port_combo.currentText()
        motion = self.motion_combo.currentText()
        try:
            count = int(self.record_count_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid number for records.")
            return

        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

        self.status_label.setText(f"Recording {count} data sets for {motion}...")
        self.record_count = 0
        self.data_set_max = count
        self.motion_assigned = motion
        self.name_index = self.find_max_number_in_filenames(motion, self.save_path) + 1

        self.serial_thread = SerialThread(port, DEF_BAUD_RATE)      # 括号内是传递的参数
        self.serial_thread.received_data.connect(self.handle_data)
        self.serial_thread.finished.connect(self.recording_finished)
        self.serial_thread.start()

        self.timer.start(100)  # Check data every 100 ms [when start record]

    def stop_recording(self):
        if self.serial_thread is not None:
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.status_label.setText("Recording stopped.")
        self.timer.stop()

    def handle_data(self, received_string): # received_string为接收的串口数据
        if self.check_title(received_string):
            filename = os.path.join(self.save_path, self.motion_assigned + DEF_FILE_NAME_SEPERATOR + str(
                self.name_index) + DEF_FILE_FORMAT)     # 拼接文件完整名称
            with open(filename, "a") as file:
                file.write(self.imu_string(received_string))
            self.status_label.setText(f"Data saved as {filename}")
            self.record_count += 1
            self.name_index += 1

            if self.record_count >= self.data_set_max:
                self.stop_recording()

    def check_title(self, received_string):
        title_buffer = received_string.split('\n')[0] + '\n' # 按换行符分割的第一个数据 再加上\n
        return title_buffer == DEF_TITLE_STRING

    def imu_string(self, received_string):
        return received_string[len(DEF_TITLE_STRING):]

    def find_max_number_in_filenames(self, motion, folder_path): # folder_path是传递参数 值为self.save_path
        max_number = 0
        number_pattern = re.compile(r'\d+')
        matching_filenames = []

        for filename in os.listdir(folder_path):
            if motion in filename:
                matching_filenames.append(filename)

        for filename in matching_filenames:
            numbers = number_pattern.findall(filename)
            for num_str in numbers:
                num = int(num_str)
                if num > max_number:
                    max_number = num

        return max_number

    def check_data(self):
        # This function is called periodically to check for incoming data
        print("Checking for data...")
        pass

    def recording_finished(self):
        self.status_label.setText("Recording completed.")
        self.timer.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())