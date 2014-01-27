#!/usr/bin/env/python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import platform
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
    log_format = "%(lineno)d: %(funcName)s, %(module)s.py, %(levelname)s: %(message)s"
else:
    logger.setLevel(logging.ERROR)
    log_format = "%(levelname)s: %(message)s"
stream = logging.StreamHandler()
fmt = logging.Formatter(log_format, datefmt="%d/%m-%H:%M")
stream.setFormatter(fmt)
logger.addHandler(stream)
debug = logger.debug
error = logger.error
warn = logger.warning


class Res:
    """
    This class creates a dict with keys to resources
    that can be included in the gui.
    It only needs to be instantiated once to populate the dict:
    >>> Res()
    The instance can be discarded.
    After that various resources can be accesed like this:
    >>> Res.icons["name"]
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

        self._setup_widgets()
        self._layout()

        self._complete = False
        return

    def _setup_widgets(self):
        self._update_path_line()

        self.path_browse_btn.clicked.connect(self._browse_path)
        debug("set path_browse_btn")

        self._update_tree()
        return

    def _layout(self):
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.path_line, 1, 1)  # row 1, col 1
        grid.addWidget(self.path_browse_btn, 1, 2)  # row 1, col 2
        grid.addWidget(self.path_tree, 2, 1, 1, 2)  # row 2, col 1, rowspan 1, colspan 2

        self.setLayout(grid)
        debug("added layout grid")
        return

    @staticmethod
    def _italic_font():
        font = QtGui.QFont()
        font.setItalic(True)
        return font

    @staticmethod
    def _red_brush():
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor("red"))
        return brush

    def _update_gui(self):
        self._update_path_line()
        self._update_tree()
        return

    def _update_path_line(self):
        debug("updating path_line")
        if self.config.input_folder is not None:
            #set already known data:
            self.path_line.setText(self.config.input_folder)
        else:
            #no data known:
            self.path_line.setPlaceholderText("Click Browse to choose path")
            #something must be set:
            self.registerField("path*", self.path_line)
        debug("set path_line")
        return

    def _update_tree(self):
        debug("updating path_tree")
        #reset tree:
        self.path_tree.reset()
        debug("tree reset")

        #tree customizations:
        self.path_tree.setItemsExpandable(True)
        self.path_tree.setIndentation(10)
        self.path_tree.setUniformRowHeights(True)
        self.path_tree.expanded.connect(lambda: self.path_tree.resizeColumnToContents(0))
        self.path_tree.collapsed.connect(lambda: self.path_tree.resizeColumnToContents(0))

        #create model:
        model = QtGui.QStandardItemModel()
        #add headers:
        model.setHorizontalHeaderLabels(["Filename", "Type"])
        #connect to top-level item:
        root = model.invisibleRootItem()

        #create parent item:
        if self.config.input_folder is not None:
            folder_name = os.path.basename(self.config.input_folder)
            top_folder = QtGui.QStandardItem(folder_name)
            top_folder.setIcon(Res.icons["folder"])
            #append parent to root:
            root.appendRow(top_folder)
            debug("set top row in tree model")

            files = Parse(self.config.input_folder)
            files = files.all_files
            debug("got all files from %s", self.config.input_folder)

            if len(files) == 0:
                debug("no valid files were found in %s", self.config.input_folder)
                #create a red, italicized label:
                name = QtGui.QStandardItem("None")
                name.setFont(self._italic_font())
                name.setForeground(self._red_brush())
                #create a red, italicized description:
                filetype = QtGui.QStandardItem("No valid files found")
                filetype.setFont(self._italic_font())
                filetype.setForeground(self._red_brush())
                #append this to the tree:
                root.appendRow([name, filetype])
                #disable next button:
                self._next_button_enabled(False)

            else:
                for file in files:
                    #go through each file in the selected folder
                    #create a name label from the item's basename:
                    name = QtGui.QStandardItem(os.path.basename(file))
                    name.setEditable(False)

                    #get file's extension and customize each extension
                    #with a different name and icon:
                    #TODO: automate the process, maybe with a dict?
                    #filetypes = {".m4a": ["MPEG-4 Audio", Res.icons["m4a file"]]
                    #             etc.}
                    ext = os.path.splitext(file)[1]
                    if ext == ".m4a":
                        filetype = QtGui.QStandardItem("MPEG-4 Audio")
                        name.setIcon(Res.icons["m4a file"])
                    elif ext == ".jpg" or ext == ".jpeg":
                        filetype = QtGui.QStandardItem("JPG Image")
                        name.setIcon(Res.icons["jpg file"])
                    elif ext == ".png":
                        filetype = QtGui.QStandardItem("PNG Image")
                        name.setIcon(Res.icons["png file"])
                    else:
                        filetype = QtGui.QStandardItem("Unknown")
                        name.setIcon(Res.icons["empty file"])
                    filetype.setTextAlignment(QtCore.Qt.AlignVCenter)
                    filetype.setEditable(False)

                    #append each file on the tree:
                    top_folder.appendRow([name, filetype])
                    debug("appended: %s, %s", name.text(), filetype.text())
                    #enable next button:
                    self._next_button_enabled(True)

        #item.setCheckable(True) #TODO: choose items
        #set the tree model:
        self.path_tree.setModel(model)
        debug("set tree model to tree")

        #expand the tree:
        self.path_tree.expandAll()
        return

    def _browse_path(self):
        debug("Browse button pressed")

        if self.config.input_folder is not None:
            #TODO: why is this not working?
            default_path = self.config.input_folder
        else:
            default_path = os.getcwd()

        #create a file dialog that disables files:
        debug("creating QFileDialog()")
        file_dlg = QtWidgets.QFileDialog()
        path = file_dlg.getExistingDirectory(self, "Choose folder", default_path,
                                             QtWidgets.QFileDialog.ShowDirsOnly)

        if path:
            debug("path from QFileDialog(): %s", path)
            if path == self.config.input_folder:
                warn("the same path was selected, ignored")
                return
            else:
                self.config.input_folder = path
                debug("updating gui")
                self._update_gui()
                return
        else:
            warn("no path selected from QFileDialog()")
            return

    def nextId(self):
        return Wizard.URLPage

    def _next_button_enabled(self, status):
        """This function sets the value of _complete, calls
        isComplete and emits a signal to the Wizard"""
        debug("next button enabling: %s", status)
        self._complete = status
        self.isComplete()
        self.completeChanged.emit()
        return

    def isComplete(self):
        """Reimplementation of QWizardPage.isComplete with
        a check of a class variable"""
        if self._complete:
            return True
        else:
            return False


class URLPage(QtWidgets.QWizardPage):
    def __init__(self, config, parent=None):
        super(URLPage, self).__init__(parent)
        debug("instantiated URLPage class")

        if not isinstance(config, Config):
            raise ValueError("config must be an instance of Config class")
        else:
            self.config = config

        self.setTitle("URL")
        self.setSubTitle("Enter an url to the Audible page with metadata for this book:")

        self.url_line = QtWidgets.QLineEdit()

        self._setup_widgets()
        self._layout()

    def _setup_widgets(self):
        if self.config.url is not None:
            self.url_line.setText(self.config.url)
        else:
            self.url_line.setPlaceholderText("Enter url...")

    def _layout(self):
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
    Res()
    wizard = Wizard(config)
    wizard.show()
    app.exec_()

if __name__ == "__main__":
    import platform

    if platform.system() == "Darwin":
        #sys.argv.append("test_ab")
        pass
    else:
        #sys.argv.append("--help")
        #sys.argv.append(r"D:\Downloads\AAC Audiobooks")
        #sys.argv.append("google.com")
        sys.argv.append("--cover")
        sys.argv.append(r"D:\Downloads\ImmPoster.jpg")

    sys.exit(main())
