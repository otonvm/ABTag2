#!/usr/bin/env/python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from argparse import ArgumentParser

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
import icons

from config import Config
from lib.util import Tools
from lib.tree import Parse

DEBUG = True
VERSION = 0.1

logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)
    log_format = "%(asctime)s - %(lineno)d: %(funcName)s, %(module)s, %(levelname)s: %(message)s"
else:
    logger.setLevel(logging.ERROR)
    log_format = "%(asctime)s - %(levelname)s: %(message)s"
stream = logging.StreamHandler()
fmt = logging.Formatter(log_format, datefmt="%d/%m-%H:%M")
stream.setFormatter(fmt)
logger.addHandler(stream)
debug = logger.debug
error = logger.error
warn = logger.warning


class Wizard(QtWidgets.QWizard):
    PathsPage = 0
    URLPage = 1

    def __init__(self, config, parent=None):
        super(Wizard, self).__init__(parent)
        debug("instantiated Wizard class")

        if not isinstance(config, Config):
            raise ValueError("config must be an instance of Config class")

        self.setModal(True)

        self.setPage(self.PathsPage, PathsPage(config))
        self.setPage(self.URLPage, URLPage(config))
        self.setStartId(self.PathsPage)

        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, self.close)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.close)


class PathsPage(QtWidgets.QWizardPage):
    def __init__(self, config):
        super(PathsPage, self).__init__()
        debug("instantiated PathsPage class")

        if not isinstance(config, Config):
            raise ValueError("config must be an instance of Config class")
        else:
            self.config = config

        self.setTitle("Audio files path")
        self.setSubTitle("Choose a path which contains audio files to tag:")

        self.path_line = QtWidgets.QLineEdit()
        self.path_browse_btn = QtWidgets.QPushButton("&Browse")
        self.path_tree = QtWidgets.QTreeView()

        self.__setup_widgets()
        self.__layout()

    def __setup_widgets(self):
        self._update_path_line()

        self.path_browse_btn.clicked.connect(self._browse_path)
        debug("set path_browse_btn")
        return

    def __layout(self):
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.path_line, 1, 1)  # row 1, col 1
        grid.addWidget(self.path_browse_btn, 1, 2)  # row 1, col 2
        grid.addWidget(self.path_tree, 2, 1, 1, 2)  # row 2, col 1, rowspan 1, colspan 2

        self.setLayout(grid)
        debug("added layout grid")
        return

    def _update_path_line(self):
        if self.config.input_folder is not None:
            self.path_line.setText(self.config.input_folder)
            self._update_tree()
        else:
            self.path_line.setPlaceholderText("Click Browse to choose path")
        debug("set path_line")
        return

    def _update_tree(self):
        #reset tree:
        self.path_tree.reset()

        #tree customizations:
        self.path_tree.setItemsExpandable(True)
        self.path_tree.setIndentation(10)
        self.path_tree.expanded.connect(lambda: self.path_tree.resizeColumnToContents(0))
        self.path_tree.collapsed.connect(lambda: self.path_tree.resizeColumnToContents(0))

        #create model:
        model = QtGui.QStandardItemModel()
        #add headers:
        model.setHorizontalHeaderLabels(["Filename", "Type"])
        #connect to top-level item:
        root = model.invisibleRootItem()
        #create parent item:
        folder_name = os.path.basename(self.config.input_folder)
        top_folder = QtGui.QStandardItem(folder_name)
        top_folder.setIcon(QtGui.QIcon(QtGui.QPixmap(":/mac/folder-mac.png")))
        #append parent to root:
        root.appendRow(top_folder)

        item = QtGui.QStandardItem("item")
        #item.setCheckable(True) #TODO: choose items
        desc = QtGui.QStandardItem("desc")
        desc.setTextAlignment(QtCore.Qt.AlignVCenter)
        top_folder.appendRow([item, desc])
        self.path_tree.setModel(model)

        return

    def _browse_path(self):
        if self.config.input_folder is not None:
            default_path = self.config.input_folder
        else:
            default_path = os.getcwd()

        file_dlg = QtWidgets.QFileDialog()
        path = file_dlg.getExistingDirectory(self, "Choose folder", default_path,
                                             QtWidgets.QFileDialog.ShowDirsOnly)

        if path:
            debug("path from QFileDialog: %s", path)
            self.config.input_folder = path
        else:
            warn("no path selected from QFileDialog")

        self._update_tree()
        self._update_path_line()
        return

    def nextId(self):
        return Wizard.URLPage


class URLPage(QtWidgets.QWizardPage):
    def __init__(self, config, parent=None):
        super(URLPage, self).__init__(parent)

        if not isinstance(config, Config):
            raise ValueError("config must be an instance of Config class")
        else:
            self.config = config

        self.setTitle("URL")
        self.setSubTitle("Enter an url to the Audible page with metadata for this book:")

        self.url_line = QtWidgets.QLineEdit()

        self.__setup_widgets()
        self.__layout()

    def __setup_widgets(self):
        if self.config.url is not None:
            self.url_line.setText(self.config.url)
        else:
            self.url_line.setPlaceholderText("Enter url...")

    def __layout(self):
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.url_line, 1, 1, 1, 2)  # row 1, col 1

        self.setLayout(grid)
        debug("added layout grid")
        return

    def nextId(self):
        return Wizard.PathsPage


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help="Display verbose information. [default: %(default)s]")

    parser.add_argument(dest='input_folder', metavar='<folder path>', action='store',
                        nargs='?', help="Input folder that contains all items.")

    parser.add_argument(dest='url', metavar='<url>', action='store', nargs='?',
                        help="url to audible page with metadata [default: None]")

    parser.add_argument('-c', '--cover', dest='input_cover', metavar='<cover image path>', action='store',
                        help="Path to a cover image. [default: None]")
    parser.add_argument('-V', '--version', action='version', version=str(VERSION))

    args = parser.parse_args()

    return args


def main():
    debug("argv: %s", sys.argv)
    debug("path: %s", sys.path)
    debug("current path: %s", os.getcwd())

    args = parse_args()
    debug("args: %s", args)

    config = Config()
    util = Tools()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        config.verbose = True

    if args.input_folder is not None:
        debug("checking %s", args.input_folder)

        try:
            if util.path_is_dir(args.input_folder):
                debug("%s is a directory", args.input_folder)
                config.input_folder = util.real_path(args.input_folder)

            else:
                warn("%s is not a folder", args.input_folder)
        except OSError as err:
            debug("error checking input_folder")
            raise SystemExit(err)

    if args.input_cover is not None:
        debug("checking %s", args.input_cover)

        try:
            if util.path_is_file(args.input_cover):
                debug("%s is a file", args.input_cover)
                config.input_cover = util.real_path(args.input_cover)

            else:
                warn("%s is not a file", args.input_cover)
        except OSError as err:
            debug("error checking input_cover")
            raise SystemExit(err)

    if args.url is not None:
        config.url = args.url

    debug("config after argparse: %s", config)

    #start gui:
    app = QtWidgets.QApplication([])
    wizard = Wizard(config)
    wizard.show()
    app.exec_()

if __name__ == "__main__":
    import platform

    if platform.system() == "Darwin":
        sys.argv.append("test_ab")
    else:
        #sys.argv.append("--help")
        sys.argv.append(r"D:\Downloads\AAC Audiobooks")
        sys.argv.append("google.com")
        sys.argv.append("--cover")
        sys.argv.append(r"D:\Downloads\ImmPoster.jpg")

    sys.exit(main())
