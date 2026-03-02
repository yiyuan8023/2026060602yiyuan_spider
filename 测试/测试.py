from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *


class Window(QMainWindow):

    def __init__(self):
        super().__init__()
        self.resize(300, 300)
        self.setWindowTitle("CAPTION")
        self.setCentralWidget(QWidget(self))
        self.create_widgets()

    def create_widgets(self):
        self.groupBox1 = QGroupBox(self)
        self.groupBox1.setGeometry(40, 16, 232, 232)
        self.groupBox1.setFont(QFont("Segoe UI", 9))
        self.groupBox1.setTitle("GroupBox")
        self.groupBox1.clicked.connect(self.groupBox1_clicked)
        pass

    def groupBox1_clicked(self, checked):

        pass


if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
