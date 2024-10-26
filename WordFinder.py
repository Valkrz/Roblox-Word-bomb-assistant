import sys
import random
import time
import win32gui
import pyautogui
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene, QGraphicsTextItem, QDialog, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor

# Load words from a text file
def load_words_from_txt(file_path):
    with open(file_path, 'r') as file:
        words = {line.strip().lower() for line in file if len(line.strip()) >= 3}
    return words

# Check if a word is alphabetic
def is_english_word(word):
    return word.isalpha()

# Find words that match criteria
def find_word_combination(input_letters, words, more_than=None, less_than=None, exact_length=None):
    if len(input_letters) < 2:
        return []
    if exact_length is not None:
        return [word for word in words if input_letters in word and is_english_word(word) and len(word) == exact_length]
    elif more_than is not None and less_than is not None:
        return [word for word in words if input_letters in word and is_english_word(word) and more_than < len(word) < less_than]
    elif more_than is not None:
        return [word for word in words if input_letters in word and is_english_word(word) and len(word) > more_than]
    elif less_than is not None:
        return [word for word in words if input_letters in word and is_english_word(word) and len(word) < less_than]
    else:
        return [word for word in words if input_letters in word and is_english_word(word) and len(word) >= 3]

class ChangeLengthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Word Length")
        self.setFixedSize(300, 200)
        self.setStyleSheet("""
            QDialog { background-color: #2E2E2E; }
            QLineEdit { background-color: #404040; color: white; border: none; border-radius: 5px; padding: 5px; }
            QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 10px; font-size: 14px; }
            QPushButton:hover { background-color: #45a049; }
            QLabel { color: white; }
        """)
        layout = QVBoxLayout(self)
        self.more_than_input = QLineEdit(self)
        self.more_than_input.setPlaceholderText("More Than (default 3)")
        layout.addWidget(self.more_than_input)
        self.less_than_input = QLineEdit(self)
        self.less_than_input.setPlaceholderText("Less Than")
        layout.addWidget(self.less_than_input)
        self.exact_length_input = QLineEdit(self)
        self.exact_length_input.setPlaceholderText("Exact Length")
        layout.addWidget(self.exact_length_input)
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

    def get_length_criteria(self):
        more_than = int(self.more_than_input.text()) if self.more_than_input.text() else 3
        less_than = int(self.less_than_input.text()) if self.less_than_input.text() else None
        exact_length = int(self.exact_length_input.text()) if self.exact_length_input.text() else None
        return more_than, less_than, exact_length

class AutotypeThread(QThread):
    autotype_signal = pyqtSignal(str)

    def __init__(self, speed, humanization, words, more_than, less_than, exact_length, main_window):
        super().__init__()
        self.speed = speed / 10000000  # Convert to seconds
        self.humanization = humanization / 10000000  # Convert to seconds
        self.words = words
        self.more_than = more_than
        self.less_than = less_than
        self.exact_length = exact_length
        self.main_window = main_window
        self.running = False

    def run(self):
        self.running = True

    def type_word(self, word):
        roblox_window = self.find_roblox_window()
        if roblox_window:
            win32gui.SetForegroundWindow(roblox_window)
        for char in word:
            if not self.running:
                break
            pyautogui.press(char)
            time.sleep(self.speed + random.uniform(0, self.humanization))

    def find_roblox_window(self):
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Roblox" in title:
                    windows.append(hwnd)
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows[0] if windows else None

    def stop(self):
        self.running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Word Finder")
        self.setGeometry(100, 100, 500, 120)
        self.setStyleSheet("""
            QMainWindow { background-color: #333; }
            QLineEdit { background-color: #404040; color: white; border: none; border-radius: 5px; padding: 5px; }
            QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 10px; font-size: 14px; }
            QPushButton:hover { background-color: #45a049; }
            QLabel { color: white; }
        """)
        
        # Load words from file
        self.words = load_words_from_txt('words.txt')
        self.more_than = 3
        self.less_than = None
        self.exact_length = None

        # Main layout setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        
        # Left layout (canvas and entry)
        left_layout = QVBoxLayout()
        self.canvas = QGraphicsView(self)
        self.canvas.setFixedSize(250, 100)
        self.canvas.setStyleSheet("background-color: #333; border: none; border-radius: 10px;")
        self.scene = QGraphicsScene(self)
        self.canvas.setScene(self.scene)
        left_layout.addWidget(self.canvas, alignment=Qt.AlignCenter)

        # Entry box
        self.entry = QLineEdit(self)
        self.entry.setFont(QFont("Roboto", 14))
        self.entry.setStyleSheet("background-color: white; color: black; border: none; border-radius: 5px; padding: 5px;")
        self.entry.setFocusPolicy(Qt.StrongFocus)
        left_layout.addWidget(self.entry, alignment=Qt.AlignCenter)
        self.entry.returnPressed.connect(self.on_enter)

        # Right layout (buttons)
        right_layout = QVBoxLayout()
        self.change_length_button = QPushButton("Change Word Length", self)
        self.change_length_button.clicked.connect(self.show_change_length_dialog)
        right_layout.addWidget(self.change_length_button)

        self.autotype_button = QPushButton("Autotype", self)
        self.autotype_button.clicked.connect(self.toggle_autotype)
        right_layout.addWidget(self.autotype_button)

        # Combine layouts
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        central_widget.setLayout(main_layout)

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.entry.setFocus()

        # Autotype settings
        self.autotype_thread = None
        self.autotype_running = False

    def on_enter(self):
        input_letters = self.entry.text().strip().lower()
        self.entry.clear()
        
        matching_words = find_word_combination(input_letters, self.words, self.more_than, self.less_than, self.exact_length)
        
        if matching_words:
            random_word = random.choice(matching_words)
            self.display_word(random_word)
            
            # Trigger autotyping with a 0.2-second delay
            if self.autotype_running:
                QTimer.singleShot(200, lambda: self.autotype_thread.type_word(random_word))
        else:
            self.display_word("No match found")

    def display_word(self, word):
        self.scene.clear()
        text_item = QGraphicsTextItem(word)
        text_item.setFont(QFont("Roboto", 20))
        text_item.setDefaultTextColor(QColor("white"))
        text_item.setPos(125 - text_item.boundingRect().width() / 2, 50 - text_item.boundingRect().height() / 2)
        self.scene.addItem(text_item)

    def show_change_length_dialog(self):
        dialog = ChangeLengthDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.more_than, self.less_than, self.exact_length = dialog.get_length_criteria()

    def toggle_autotype(self):
        if self.autotype_running:
            self.stop_autotype()
            self.autotype_button.setStyleSheet("background-color: #FF5722;")
        else:
            self.start_autotype()
            self.autotype_button.setStyleSheet("background-color: #4CAF50;")
        
    def start_autotype(self):
        if not self.autotype_thread:
            speed = 1  # Set to the minimum speed (effectively fast)
            humanization = 0  # Set to the minimum humanization (no variation)
            self.autotype_thread = AutotypeThread(speed, humanization, self.words, self.more_than, self.less_than, self.exact_length, self)
            self.autotype_thread.start()
            self.autotype_running = True

    def stop_autotype(self):
        if self.autotype_thread:
            self.autotype_thread.stop()
            self.autotype_thread.wait()
            self.autotype_thread = None
            self.autotype_running = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
