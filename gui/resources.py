# -*- coding: utf-8 -*-

import platform

from PyQt5 import QtGui

import icons


class Icons:
    """
    This class creates a dict with keys to resources
    that can be included in the gui.
    It only needs to be instantiated once to populate the dict:
    >>> Icons()
    The instance can be discarded.
    After that various resources can be accesed like this:
    >>> Icons.icons["name"]
    This returns a QPixmap object.
    """
    icons = {}

    def __init__(self):
        icons.load()

        if platform.system() == "Darwin":
            self.icons["folder"] = QtGui.QIcon(QtGui.QPixmap(":/mac/folder.png"))
            self.icons["empty file"] = QtGui.QIcon(QtGui.QPixmap(":/mac/empty.png"))
            self.icons["m4a file"] = QtGui.QIcon(QtGui.QPixmap(":/win/warning.png"))
            self.icons["jpg file"] = QtGui.QIcon(QtGui.QPixmap(":/mac/jpeg.png"))
            self.icons["png file"] = QtGui.QIcon(QtGui.QPixmap(":/win/warning.png"))
        if platform.system() == "Windows":
            self.icons["folder"] = QtGui.QIcon(QtGui.QPixmap(":/win/folder.png"))
            self.icons["empty file"] = QtGui.QIcon(QtGui.QPixmap(":/win/empty.png"))
            self.icons["m4a file"] = QtGui.QIcon(QtGui.QPixmap(":/win/warning.png"))
            self.icons["jpg file"] = QtGui.QIcon(QtGui.QPixmap(":/win/jpg.png"))
            self.icons["png file"] = QtGui.QIcon(QtGui.QPixmap(":/win/png.png"))
