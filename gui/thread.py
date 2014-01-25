#!/usr/bin/env/python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QThread


class Thread(QThread):
    def __init__(self, parent=None):
        super(Thread, self)__init__(parent)

    def run(self):
        pass
