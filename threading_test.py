#!/usr/bin/env/python3
# -*- coding: utf-8 -*-

from PyQt5 import QtCore
from PyQt5 import QtWidgets

import time


class Window(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.list_widget = QtWidgets.QListWidget()
        self.button = QtWidgets.QPushButton("Start")
        self.button.clicked.connect(self.start)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.thread1 = Worker(1)
        self.thread1.progress.connect(self.progress)
        self.thread1.done.connect(self.recieve)

        self.thread2 = Worker(2)
        self.thread2.progress.connect(self.progress)
        self.thread2.done.connect(self.recieve)

        self.show()

    def start(self):
        self.thread1.start()
        #self.thread1.wait()
        self.thread2.start()
        #self.thread2.wait()

    @QtCore.pyqtSlot(str)
    def recieve(self, val):
        print("received:", val)

    @QtCore.pyqtSlot(str)
    def progress(self, val):
        self.list_widget.addItem(val)


class Worker(QtCore.QThread):
    progress = QtCore.pyqtSignal(str)
    done = QtCore.pyqtSignal(str)

    def __init__(self, pause, parent=None):
        super(Worker, self).__init__(parent)

        self.pause = pause

    def __del__(self):
        self.wait()

    def run(self):
        for i in range(5):
            self.progress.emit("in thread {}: {}".format(self.currentThreadId(), i))
            time.sleep(self.pause)
        self.done.emit("done")


def main():
    app = QtWidgets.QApplication([])
    window = Window()
    app.exec_()

if __name__ == "__main__":
    main()
