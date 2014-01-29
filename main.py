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
        self.setFixedSize(700, 550)

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

        self._path_line = QtWidgets.QLineEdit()
        self.path_browse_btn = QtWidgets.QPushButton("&Browse")
        self._path_tree = QtWidgets.QTreeView()
        self._files = None
        self._complete = False

        self._setup_widgets()
        self._setup_layout()

        self._get_files()
        self._update_path_line()
        self._update_tree()

    def _setup_widgets(self):
        self.path_browse_btn.clicked.connect(self._browse_path)
        debug("set path_browse_btn")

        #something must be set:
        self.registerField("path*", self._path_line)

        #tree customizations:
        self._path_tree.setItemsExpandable(True)
        self._path_tree.setIndentation(10)
        self._path_tree.setUniformRowHeights(True)
        self._path_tree.expanded.connect(lambda: self._path_tree.resizeColumnToContents(0))
        self._path_tree.collapsed.connect(lambda: self._path_tree.resizeColumnToContents(0))
        return

    def _setup_layout(self):
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self._path_line, 1, 1)  # row 1, col 1
        grid.addWidget(self.path_browse_btn, 1, 2)  # row 1, col 2
        grid.addWidget(self._path_tree, 2, 1, 1, 2)  # row 2, col 1, rowspan 1, colspan 2

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
        self._get_files()
        self._update_path_line()
        self._update_tree()
        return

    def _update_path_line(self):
        debug("updating _path_line")
        if self.config.input_folder is not None:
            #set already known data:
            self._path_line.setText(self.config.input_folder)
        else:
            #no data known:
            self._path_line.setPlaceholderText("Click Browse to choose path")
        debug("set _path_line")
        return

    def _get_files(self):
        if self.config.input_folder is not None:
            #get all files in the folder:
            files = Parse(self.config.input_folder)
            self._files = files.all_files
            debug("got all files from %s", self.config.input_folder)
            return
        else:
            #do nothing
            return

    def _update_tree(self):
        debug("updating _path_tree")

        #reset tree:
        self._path_tree.reset()
        debug("_path_tree reset")

        #create model:
        model = QtGui.QStandardItemModel()
        #add headers:
        model.setHorizontalHeaderLabels(["Filename", "Type"])
        debug("created QStandardItemModel model")

        #connect to top-level item:
        tree_root = model.invisibleRootItem()

        debug("tree reset")

        if self._files is not None:
            #set a top_folder object for root:
            folder_name = os.path.basename(self.config.input_folder)
            top_folder = QtGui.QStandardItem(folder_name)
            top_folder.setIcon(Res.icons["folder"])

            #append top folder parent to root:
            tree_root.appendRow(top_folder)
            debug("set top row in tree model")

            self._path_tree.setModel(model)

            for file in self._files:
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

            self._next_button_enabled(True)

        elif self.config.input_folder is not None:
            debug("no files in _files")

            #set tree to an empty model:
            self._path_tree.setModel(model)
            debug("set model to tree")

            #create a red, italicized label:
            name = QtGui.QStandardItem("None")
            name.setFont(self._italic_font())
            name.setForeground(self._red_brush())
            name.setEditable(False)

            #create a red, italicized description:
            filetype = QtGui.QStandardItem("No valid files found")
            filetype.setFont(self._italic_font())
            filetype.setForeground(self._red_brush())
            filetype.setEditable(False)

            #append this to the tree:
            tree_root.appendRow([name, filetype])
            #disable next button:
            self._next_button_enabled(False)

        #expand the tree:
        self._path_tree.expandAll()
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
                self._update_gui()
                return
        else:
            warn("no path selected from QFileDialog()")
            return

    def nextId(self):
        return Wizard.URLPage

    def _next_button_enabled(self, status):
        """This function sets the value of _complete
        and emits a signal to the Wizard"""
        debug("next button enabling: %s", status)
        self._complete = status
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
        self.setSubTitle("Enter an audible url that points to the metadata of your book.")

        self._main_layout = QtWidgets.QVBoxLayout()
        self._main_layout.setSpacing(10)

        self._url_edit = QtWidgets.QLineEdit()
        self._reload_button = QtWidgets.QPushButton()
        self._title_edit = QtWidgets.QLineEdit()
        self._authors_edit = QtWidgets.QLineEdit()
        self._narrators_edit = QtWidgets.QLineEdit()
        self._series_edit = QtWidgets.QLineEdit()
        self._series_no_edit = QtWidgets.QLineEdit()
        debug("added all widgets")

        self._add_single_line_widget("URL", self._url_edit)
        self._add_line_and_reload_button_widget()
        self._add_single_line_widget("Title", self._title_edit)
        self._add_single_line_widget("Authors", self._authors_edit)
        self._add_single_line_widget("Narrators", self._narrators_edit)
        self._add_series_widget()

        self.setLayout(self._main_layout)

    @staticmethod
    def _label_font():
        label_font = QtGui.QFont()
        label_font.setPixelSize(10)
        label_font.setBold(True)
        return label_font

    def _add_single_line_widget(self, label, widget):
        debug("adding widget: %s, label: %s", widget, label)

        size_policy_min = QtWidgets.QSizePolicy("Minimum")

        group_box = QtWidgets.QGroupBox()
        group_box.setTitle(label)
        group_box.setFlat(True)
        group_box.setFont(self._label_font())
        group_box.setSizePolicy(size_policy_min)

        group_box_layout = QtWidgets.QHBoxLayout()
        group_box_layout.addWidget(widget)
        group_box_layout.setContentsMargins(0, 5, 0, 0)
        group_box_layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)

        group_box.setLayout(group_box_layout)

        self._main_layout.addWidget(group_box)

    def _add_line_and_reload_button_widget(self):
        #customize (create) line:
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

        #fixed_policy = QtWidgets.QSizePolicy()
        #customize button:
        self._reload_button.setText("&Reload")
        self._reload_button.setSizePolicy(QtWidgets.QSizePolicy())

        #create layout for both:
        line_btn_layout = QtWidgets.QHBoxLayout()
        line_btn_layout.addWidget(line)
        line_btn_layout.addWidget(self._reload_button)

        self._main_layout.addLayout(line_btn_layout)

    def _add_series_widget(self):
        debug("adding series wiget")

        size_policy_min = QtWidgets.QSizePolicy("Minimum")

        series_layout = QtWidgets.QHBoxLayout()

        series_title_box = QtWidgets.QGroupBox()
        series_title_box.setTitle("Series")
        series_title_box.setFlat(True)
        series_title_box.setFont(self._label_font())
        series_title_box.setSizePolicy(size_policy_min)

        series_title_layout = QtWidgets.QHBoxLayout()
        series_title_layout.addWidget(self._series_edit)
        #series_title_layout.setContentsMargins(0, 5, 0, 0)
        series_title_layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)

        series_title_box.setLayout(series_title_layout)

        series_layout.addWidget(series_title_box)

        series_no_box = QtWidgets.QGroupBox()
        series_no_box.setTitle("Nº")
        series_no_box.setFlat(True)
        series_no_box.setFont(self._label_font())
        series_no_box.setSizePolicy(size_policy_min)

        series_no_layout = QtWidgets.QHBoxLayout()
        series_no_layout.addWidget(self._series_no_edit)
        #series_no_layout.setContentsMargins(0, 5, 0, 0)
        series_no_layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)

        series_no_box.setLayout(series_no_layout)

        series_layout.addWidget(series_no_box)

        self._main_layout.addLayout(series_layout)

"""
class URLPage2(QtWidgets.QWizardPage):
    def __init__(self, config, parent=None):
        super(URLPage, self).__init__(parent)
        debug("instantiated URLPage class")

        if not isinstance(config, Config):
            raise ValueError("config must be an instance of Config class")
        else:
            self.config = config

        self.setTitle("URL")
        self.setSubTitle("Enter an url to the Audible page with metadata for this book:")

        self._url_line = QtWidgets.QLineEdit()
        self._line = QtWidgets.QFrame()
        self._reload_btn = QtWidgets.QPushButton()
        self._label_title = QtWidgets.QLabel()
        self._edit_title = QtWidgets.QLineEdit()
        self._label_authors = QtWidgets.QLabel()
        self._edit_authors = QtWidgets.QLineEdit()
        self._label_narrators = QtWidgets.QLabel()
        self._edit_narrators = QtWidgets.QLineEdit()

        self._series_label = QtWidgets.QLabel()
        self._edit_series = QtWidgets.QLineEdit()
        self._series_no_label = QtWidgets.QLabel()
        self._edit_series_no = QtWidgets.QLineEdit()

        self._date_label = QtWidgets.QLabel()
        self._edit_date = QtWidgets.QLineEdit()
        self._description_label = QtWidgets.QLabel()
        self._edit_description = QtWidgets.QPlainTextEdit()
        self._copyright_label = QtWidgets.QLabel()
        self._edit_copyright = QtWidgets.QLineEdit()

        self._setup_widgets()
        self._layout()

    def _setup_widgets(self):
        if self.config.url is not None:
            self._url_line.setText(self.config.url)
        else:
            self._url_line.setPlaceholderText("Enter url...")

        self._line.setFrameShape(QtWidgets.QFrame.HLine)
        self._line.setFrameShadow(QtWidgets.QFrame.Sunken)

        fixed_policy = QtWidgets.QSizePolicy()

        self._reload_btn.setText("&Reload")
        self._reload_btn.setSizePolicy(fixed_policy)

        self._label_title.setText("Title:")
        self._label_title.setSizePolicy(fixed_policy)

        self._label_authors.setText("Authors:")
        self._label_authors.setSizePolicy(fixed_policy)

        self._label_narrators.setText("Narrators:")
        self._label_narrators.setSizePolicy(fixed_policy)

        self._series_label.setText("Series:")
        self._series_label.setSizePolicy(fixed_policy)

        self._series_no_label.setText("N°:")
        self._series_no_label.setSizePolicy(fixed_policy)

        self._edit_series_no.setMaxLength(2)
        self._edit_series_no.setMaximumWidth(40)

        self._date_label.setText("Date:")
        self._date_label.setSizePolicy(fixed_policy)

        self._description_label.setText("Description:")

        self._copyright_label.setText("Copyright:")
        self._copyright_label.setSizePolicy(fixed_policy)

    def _layout(self):
        layout = QtWidgets.QVBoxLayout()
        grid_top = QtWidgets.QGridLayout()
        grid_middle = QtWidgets.QGridLayout()
        grid_botttom = QtWidgets.QGridLayout()

        grid_top.addWidget(self._url_line, 1, 1, 1, 5)  # row, col, rowspan, colspan
        grid_top.addWidget(self._line, 2, 1, 1, 4)
        grid_top.addWidget(self._reload_btn, 2, 5, 1, 1)

        grid_middle.addWidget(self._label_title, 1, 1, 1, 1)
        grid_middle.addWidget(self._edit_title, 1, 2, 1, 3)

        grid_middle.addWidget(self._label_authors, 2, 1, 1, 1)
        grid_middle.addWidget(self._edit_authors, 2, 2, 1, 3)

        grid_middle.addWidget(self._label_narrators, 3, 1, 1, 1)
        grid_middle.addWidget(self._edit_narrators, 3, 2, 1, 3)

        grid_middle.addWidget(self._series_label, 4, 1, 1, 1)
        grid_middle.addWidget(self._edit_series, 4, 2, 1, 1)

        grid_middle.addWidget(self._series_no_label, 4, 3, 1, 1)
        grid_middle.addWidget(self._edit_series_no, 4, 4, 1, 1)

        grid_middle.addWidget(self._date_label, 5, 1, 1, 1)
        grid_middle.addWidget(self._edit_date, 5, 2, 1, 1)

        grid_botttom.addWidget(self._description_label, 1, 1, 1, 1)
        grid_botttom.addWidget(self._edit_description, 2, 1, 1, 4)

        grid_botttom.addWidget(self._copyright_label, 3, 1, 1, 1)
        grid_botttom.addWidget(self._edit_copyright, 3, 2, 1, 3)

        layout.addLayout(grid_top)
        layout.addLayout(grid_middle)
        layout.addLayout(grid_botttom)
        self.setLayout(layout)
        debug("added layout grid")
        return

    def nextId(self):
        return Wizard.PathsPage
"""

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
        sys.argv.append("test_ab")
        pass
    else:
        #sys.argv.append("--help")
        #sys.argv.append(r"D:\Downloads\AAC Audiobooks")
        #sys.argv.append("google.com")
        #sys.argv.append("--cover")
        #sys.argv.append(r"D:\Downloads\ImmPoster.jpg")
        sys.argv.append("test_ab")
        pass

    sys.exit(main())
