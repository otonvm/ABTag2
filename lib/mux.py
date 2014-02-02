# -*- coding: utf-8 -*-

import os
import stat
import logging
import subprocess
import platform

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from lib.tree import Tools

DEBUG = True

#logging is enabled only for debugging
logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)
    log_format = "%(lineno)d: %(funcName)s, %(module)s.py, %(levelname)s: %(message)s"
    fmt = logging.Formatter(log_format)
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
else:
    stream = logging.NullHandler()
logger.addHandler(stream)
debug = logger.debug


class Test(QtCore.QThread):
    retcode = QtCore.pyqtSignal(int)
    error = QtCore.pyqtSignal(str)

    def __init__(self, bin_path, parent=None):
        super().__init__(parent)
        debug("initialized Test")

        self._bin_path = bin_path
        self._cmd = []

    def test(self):
        self._cmd = [self._bin_path, "-h", "general"]
        self.start()

    def run(self):
        debug("testing with cmd: %s", self._cmd)

        try:
            popen = subprocess.Popen(self._cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stderr, stdout = popen.communicate(timeout=2)
            debug("subprocess stderr: %s; stdout: %s", stderr, stdout)

            retcode = popen.returncode
            debug("subprocess returncode: %s", retcode)

            if retcode != 0:
                self.retcode.emit(retcode)

        except subprocess.TimeoutExpired:
            self.error.emit("timeout")


class Demux(QtCore.QThread):
    retcode = QtCore.pyqtSignal(int)
    error = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal([int], [str])

    def __init__(self, bin_path, parent=None):
        super().__init__(parent)
        debug("initialized Demux")

        self._bin_path = bin_path
        self._cmd = []

    def demux(self, file, aac_file):
        self._cmd = [self._bin_path, "-raw", "1", file, "-out", aac_file]

        self._delete(aac_file)

        self.start()

    @staticmethod
    def _delete(file):
        try:
            os.remove(file)
        except OSError:
            pass

    def run(self):
        debug("running cmd: %s", self._cmd)

        if platform.system() == "Windows":
            start_index = 15
            stop_index = 17
        else:
            start_index = 14
            stop_index = 16

        try:
            proc = subprocess.Popen(self._cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            while proc.poll() != 0:
                line = proc.stderr.read(46).decode('utf-8')
                debug("line: %s", line)

                if line:
                    if "Error" in line:
                        output = proc.stderr.readline().decode('utf-8').strip()
                        error = output.split(': ')[1]
                        self.error.emit(error)

                    try:
                        line_slice = line[start_index:stop_index]
                        debug("line_slice: %s", line_slice)

                        number = int(line_slice)
                        debug("number: %s", number)

                        if number >= 0:
                            self.progress.emit(number)
                        else:
                            self.progress.emit(0)
                    except ValueError:
                        pass
                else:
                    self.progress.emit(100)
                    self.progress.emit("done")
            self.retcode.emit(proc.poll())
        except Exception as err:
            self.error.emit(err)


class MP4BoxError(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg


class MP4Box(QtCore.QObject):
    retcode = QtCore.pyqtSignal(int)
    error = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(int)

    def __init__(self, bin_path):
        super().__init__(None)
        self._tools = Tools()
        self._bin_path = self._tools.real_path(bin_path)
        debug("_bin_path realpath: %s", self._bin_path)

        self._signal = 0
        self._cmd = []
        self._file_path = ""
        self._file_name = ""
        self._aac_file = ""
        self._m4b_file = ""
        self._position = 0

        self._test = Test(self._bin_path)
        self._test.retcode.connect(self._retcode)
        self._test.error.connect(self._error)

        self._demux = Demux(self._bin_path)
        self._demux.retcode.connect(self._retcode_silent)
        self._demux.error.connect(self._error_silent)
        self._demux.progress.connect(self._progress)

    def test(self):
        debug("testing %s", self._bin_path)

        if self._tools.path_exists(self._bin_path):
            if not os.access(self._bin_path, os.X_OK):
                debug("%s is not executable", self._bin_path)
                os.chmod(self._bin_path, stat.S_IXUSR | stat.S_IXGRP)

            self._test.test()

        else:
            self._error("cannot find mp4box binary")

    @QtCore.pyqtSlot(int)
    def _retcode(self, code):
        debug("got returncode: %s", code)

        self.retcode.emit(code)

    @QtCore.pyqtSlot(int)
    def _retcode_silent(self, code):
        debug("got returncode: %s", code)

    @QtCore.pyqtSlot(str)
    def _error(self, msg):
        debug("got error: %s", msg)

        self.error.emit(msg)

    @QtCore.pyqtSlot(str)
    def _error_silent(self, msg):
        debug("got error: %s", msg)

    @QtCore.pyqtSlot(int)
    def _progress(self, progress):
        debug("got progress no: %s", progress)

        self.progress.emit(progress)

    def _remux(self, part_no):
        if platform.system() == "Windows":
            start_index = 10
            stop_index = 12
        else:
            start_index = 9
            stop_index = 11

        self._delete(self._m4b_file)

        self._cmd = [self._bin_path, "-brand", "M4B ", "-ab", "mp71", "-ipod", "-add",
                     "{}:name=Part {}:lang=eng".format(self._aac_file, part_no), self._m4b_file]

        try:
            proc = subprocess.Popen(self._cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

            imported = False
            while not imported and proc.poll() != 0:
                line = proc.stderr.read(47).decode('utf-8')
                debug("line %s", line)

                if line:
                    if "Error" in line:
                        output = proc.stderr.readline().decode('utf-8').strip()
                        error = output.split(': ')[1]
                        raise MP4BoxError(error)

                    try:
                        line_slice = line[start_index:stop_index]
                        debug("line_slice %s", line_slice)

                        number = int(line_slice)
                        debug("number %s", number)

                        if number >= 0 and number < 95:
                            self._position_emit(number)

                        #hack for ignoring remuxing phase
                        #it's usually so fast that it doesn't really matter
                        elif number >= 95:
                            self._position_emit(100)
                            imported = True  # break the while loop

                        else:
                            self._position_emit(0)

                    except ValueError:
                        pass
                else:
                    self._position_emit(100)
            proc.communicate()  # needed to deblock the process
            return proc.wait()
        except:
            raise

    def remux(self, file, part_no=1):
        if not isinstance(part_no, int):
            raise TypeError("part_no must be of type int")

        self._file_path, self._file_name = os.path.split(file)
        self._file_name = os.path.splitext(self._file_name)[0]

        self._aac_file = r"{}_demux.aac".format(os.path.join(self._file_path, self._file_name))
        self._m4b_file = r"{}_temp.m4b".format(os.path.join(self._file_path, self._file_name))

        self._demux.demux(file, self._aac_file)


        """
        if self._demux(file) == 0:
            if self._remux(part_no) == 0:
                self._delete(self._aac_file)
                return True
            else:
                self._delete(self._aac_file)
                self._delete(self._m4b_file)
                return False
        else:
            self._delete(self._aac_file)
            self._delete(self._m4b_file)
            return False"""
