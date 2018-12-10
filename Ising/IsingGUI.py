from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

if __name__ == '__main__':
    def exit_button_clicked():
        QCoreApplication.instance().quit()

    app = QApplication([])

    N = 100
    primary_color = QColor(Qt.black)

    canvas = QLabel()
    canvas.setPixmap(QPixmap(N,N))
    canvas.pixmap().fill(primary_color)

    button1 = QPushButton('These')
    button2 = QPushButton('buttons')
    button3 = QPushButton('do')
    button4 = QPushButton('nothing!')
    exit_button = QPushButton('EXIT!')
    exit_button.clicked.connect(exit_button_clicked)

    vb = QVBoxLayout()
    vb.addWidget(button1)
    vb.addWidget(button2)
    vb.addWidget(button3)
    vb.addWidget(button4)
    vb.addWidget(exit_button)

    hb = QHBoxLayout()
    hb.addLayout(vb)
    hb.addWidget(canvas)

    w = QWidget()
    w.setLayout(hb)

    w.show()
    app.exec()
