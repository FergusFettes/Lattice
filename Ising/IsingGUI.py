from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        primary_color = QColor(Qt.black)

        canvas = QLabel()
        canvas.setPixmap(QPixmap(N * 4, N * 4))
        canvas.pixmap().fill(primary_color)

        button1 = QPushButton('These')
        button2 = QPushButton('buttons')
        button3 = QPushButton('do')
        button4 = QPushButton('nothing!')
        exit_button = QPushButton('EXIT!')
        exit_button.clicked.connect(self.exit_button_clicked)

        vb = QVBoxLayout()
        vb.addWidget(button1)
        vb.addWidget(button2)
        vb.addWidget(button3)
        vb.addWidget(button4)
        vb.addStretch()
        vb.addWidget(exit_button)

        hb = QHBoxLayout()
        # vb.setStretch(1, 1)
        hb.addLayout(vb)
        # canvas.setSizePolicy(QSizePolicy.setHorizontalStretch(QSizePolicy, 3))
        hb.addWidget(canvas)

        self.setLayout(hb)
        self.show()

    def exit_button_clicked(self):
        QCoreApplication.instance().quit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            QCoreApplication.instance().quit()


if __name__ == '__main__':

    app = QApplication([])
    N = 100
    w = MainWindow()
    app.exec()
