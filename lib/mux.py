# -*- coding: utf-8 -*-

import os
import io
import stat
import logging
import subprocess

from PyQt5 import QtCore

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
    progress = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(str)

    def __init__(self, bin_path, parent=None):
        super().__init__(parent)
        debug("initialized Demux")

        self._bin_path = bin_path
        self._cmd = []
        self._job_cache = []

    def _emit_job(self, job):
        #check if the job has already been emitted:
        if job in self._job_cache:
            pass
        else:
            #if not emit it and add it to the cache:
            self.status.emit(job)
            self._job_cache.append(job)

    def demux(self, file, aac_file):
        self._cmd = [self._bin_path, "-raw", "1", file, "-out", aac_file]

        MP4Box.delete(aac_file)

        self.start()

    def _subproc(self):
        try:
            proc = subprocess.Popen(self._cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
            for line in io.open(proc.stderr.fileno()):
                yield line.strip()
        except subprocess.SubprocessError as err:
            self.error.emit(err)

    def run(self):
        debug("running cmd: %s", self._cmd)

        for line in self._subproc():
            if line:
                debug("demux current line: %s", line)

                self._emit_job("Media Export")

                line_slice = line[38:40].strip()
                if line_slice:
                    try:
                        self.progress.emit(int(line_slice))
                    except ValueError:
                        self.error.emit(line)
                        break
        else:
            self.progress.emit(100)
            self.quit()


class Remux(QtCore.QThread):
    retcode = QtCore.pyqtSignal(int)
    error = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(str)
    #finished = QtCore.pyqtSignal()

    def __init__(self, bin_path, parent=None):
        super().__init__(parent)
        debug("initialized Demux")

        self._job_cache = []
        self._bin_path = bin_path
        self._m4b_file = ""
        self._cmd = []

    def remux(self, aac_file, m4b_file, part_no):
        self._cmd = [self._bin_path, "-brand", "M4B ", "-ab", "mp71", "-ipod", "-add",
                     "{}:name=Part {}:lang=eng".format(aac_file, part_no), m4b_file]

        MP4Box.delete(m4b_file)

        self.start()

    def _emit_job(self, job):
        #check if the job has already been emitted:
        if job in self._job_cache:
            pass
        else:
            #if not emit it and add it to the cache:
            self.status.emit(job)
            self._job_cache.append(job)

    def _subproc(self):
        try:
            proc = subprocess.Popen(self._cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
            for line in io.open(proc.stderr.fileno()):
                yield line.strip()
        except subprocess.SubprocessError as err:
            self.error.emit(err)

    def run(self):
        debug("running cmd: %s", self._cmd)

        for line in self._subproc():
            if line:
                debug("remux current line: %s", line)

                #first operation:
                if "Importing AAC" in line:
                    #emit the current job:
                    self._emit_job("Importing AAC")

                    line_slice = line[39:41].strip()
                    if line_slice:
                        try:
                            self.progress.emit(int(line_slice))
                        except ValueError:
                            self.error.emit(line)
                            break

                #second operation:
                elif "ISO File Writing" in line:
                    self._emit_job("ISO File Writing")

                    line_slice = line[42:44].strip()
                    if line_slice:
                        try:
                            self.progress.emit(int(line_slice))
                        except ValueError:
                            self.error.emit(line)
                            break
        else:
            print("OUT!")
            self.progress.emit(100)
            self.quit()
            #self.finished.emit()


class MP4Box(QtCore.QObject):
    error = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(int)
    done = QtCore.pyqtSignal()
    message = QtCore.pyqtSignal(str)

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
        self._error_msg = ""
        self._status = ""
        self._part_no = 0
        self._current_job = None

        self.called = 0

        self._test = Test(self._bin_path)
        self._test.retcode.connect(self._recieve_retcode)
        self._test.error.connect(self._recieve_error)

        #setup demux thread:
        self._demux = Demux(self._bin_path)
        #recieve and process returncode, error and status messages:
        self._demux.error.connect(self._recieve_error)
        self._demux.status.connect(self._recieve_status)
        #passthrough progress status:
        self._demux.progress.connect(self._emit_progress)
        #control flow:
        self._demux.finished.connect(self._launch_remux_thread)

        #setup remux thread:
        self._remux = Remux(self._bin_path)
        #recieve and process returncode, error and status messages:
        self._remux.error.connect(self._recieve_error)
        self._remux.status.connect(self._recieve_status)
        #passthrough progress status:
        self._remux.progress.connect(self._emit_progress)
        #control flow:
        self._remux.finished.connect(self._finish_cleanup)

    @staticmethod
    def delete(file):
        try:
            os.remove(file)
        except OSError:
            pass

    def test(self):
        debug("testing %s", self._bin_path)

        if self._tools.path_exists(self._bin_path):
            if not os.access(self._bin_path, os.X_OK):
                debug("%s is not executable", self._bin_path)
                os.chmod(self._bin_path, stat.S_IXUSR | stat.S_IXGRP)

            self._test.test()

        else:
            self._error("cannot find mp4box binary")

##############################################################
#################       SIGNALS       ########################
##############################################################
    def _emit_error(self, msg):
        debug("got error signal: %s", msg)
        self.msg_error.emit("Error: {}".format(msg))

##############################################################
#################        SLOTS        ########################
##############################################################
    @QtCore.pyqtSlot(int)
    def _recieve_retcode(self, code):
        #recieve and emit returncode:
        debug("got returncode signal: %s", code)
        self.retcode.emit(code)

    @QtCore.pyqtSlot(str)
    def _recieve_error(self, msg):
        #recieve and process error messages:
        debug("got error signal: %s", msg)
        self._demux.finished.disconnect(self._launch_remux_thread)
        self.error.emit("Error: {}".format(msg))
        self.exit_thread()

    @QtCore.pyqtSlot(str)
    def _recieve_status(self, msg):
        #recieve and store status messages:
        debug("got status signal: %s", msg)
        self.message.emit("Thread reports: {}".format(msg))

    @QtCore.pyqtSlot(int)
    def _emit_progress(self, progress):
        #passthrough progress status:
        self.progress.emit(progress)

    @QtCore.pyqtSlot()
    def exit_thread(self):
        #when the signal is recieved launch the function
        #that stops the current_job thread:
        self._current_job.terminate()

        #disconnect all signals and delete objects:
        self._demux.disconnect()
        del self._demux

        self._remux.disconnect()
        del self._remux

        #emit all finalizing messages:
        self.progress.emit(100)
        self.error.emit("Interrupted")
        self.done.emit()

##############################################################
#################        FLOW         ########################
##############################################################
    def remux(self, file, part_no=1):
        if not isinstance(part_no, int):
            raise ValueError("part_no must be of type int")
        else:
            self._part_no = part_no

        #setup paths and file names for files:
        self._file_path, self._file_name = os.path.split(file)
        self._file_name = os.path.splitext(self._file_name)[0]

        self._aac_file = r"{}_demux.aac".format(os.path.join(self._file_path, self._file_name))
        self._m4b_file = r"{}_temp.m4b".format(os.path.join(self._file_path, self._file_name))

        #start the demux thread:
        self.message.emit("Demuxing file {}".format(file))
        self._launch_demux_thread(file)

    def _launch_demux_thread(self, file):
        #start the demux thread:
        self._demux.demux(file, self._aac_file)
        #set current job to point to the current thread:
        self._current_job = self._demux

    @QtCore.pyqtSlot()
    def _launch_remux_thread(self):
        #when the demux thread emits the finished signal
        #start the remux thread:
        self.message.emit("Created file: {}".format(self._aac_file))
        self.message.emit("Remuxing to file: {}".format(self._m4b_file))

        self._remux.remux(self._aac_file, self._m4b_file, self._part_no)
        #set current job to point to the current thread:
        self._current_job = self._remux

    @QtCore.pyqtSlot()
    def _finish_cleanup(self):
        #when the remux thread emits the finished signal
        #perform the final cleanups and emit the main
        #finished signal for this module:
        self.message.emit("Created file: {}".format(self._m4b_file))
        self.delete(self._aac_file)

        self.message.emit("Done!")
        self.done.emit()
