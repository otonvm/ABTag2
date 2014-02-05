# -*- coding: utf-8 -*-

import os
import io
import re
import logging
import subprocess

from PyQt5 import QtCore

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
            with subprocess.Popen(self._cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:

                stderr, stdout = proc.communicate(timeout=2)
                debug("subprocess stderr: %s; stdout: %s", stderr, stdout)

                retcode = proc.returncode
                debug("subprocess returncode: %s", retcode)

                if retcode != 0:
                    self.error.emit("error")
                    self.retcode.emit(retcode)

        except subprocess.TimeoutExpired:
            self.error.emit("timeout")


class Tagger(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)
    returncode = QtCore.pyqtSignal(int)

    def __init__(self, bin_path, parent=None):
        super().__init__(parent)
        debug("initialized Tagger")

        self._bin_path = bin_path
        self._cmd = []
        self._job_cache = []
        self._returncode = 0

    def tag(self, cmd):
        if not isinstance(cmd, list):
            raise ValueError("cmd must be a list")

        self._cmd.append(self._bin_path)
        self._cmd.extend(cmd)
        debug("_cmd: %s", self._cmd)

        self.start()

    def _subproc(self):
        try:
            with subprocess.Popen(self._cmd, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, bufsize=1) as proc:
                with io.open(proc.stdout.fileno()) as stdout:
                    for line in stdout:
                        yield line.strip()
                    else:
                        self._returncode = proc.poll()
                        self.returncode.emit(self._returncode)

        except subprocess.SubprocessError as err:
            self.error.emit(err)
        except OSError:
            pass

    def run(self):
        debug("started thread Tag")

        last_line = ""
        for line in self._subproc():
            debug("current line: %s", line)
            last_line = line

            try:
                match = re.search(r"\s(\d+)%\s", line).group(1)
                self.progress.emit(int(match))
            except AttributeError:
                pass

        else:
            self.progress.emit(100)
            if self._returncode != 0 and self._returncode is not None:
                self.status.emit(last_line)

            self.quit()


class Tag(QtCore.QObject):
    error = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    message = QtCore.pyqtSignal(str)
    returncode = QtCore.pyqtSignal(int)

    def __init__(self, bin_path, parent=None):
        super().__init__(parent)

        self._bin_path = bin_path
        self._tested = False

        self._file_path = ""
        self._file_name = ""
        self._m4b_temp_file = ""
        self._m4b_file = ""
        self._cmd = []

        self._test_thread = None
        self._tag_thread = None

    def reset(self):
        self._file_path = ""
        self._file_name = ""
        self._m4b_temp_file = ""
        self._m4b_file = ""
        self._cmd = []

        self._test_thread = None
        self._tag_thread = None

    @staticmethod
    def delete(file):
        try:
            os.remove(file)
        except OSError:
            pass

    def test(self):
        if self._tested:
            return

        self._test_thread = Test(self._bin_path)
        self._test_thread.retcode.connect(self._receive_emit_error)
        self._test_thread.error.connect(self._receive_emit_error)
        self._test_thread.finished.connect(self._test_finished)
        self._test_thread.test()

    @QtCore.pyqtSlot()
    def _test_finished(self):
        self._test_thread.disconnect()
        self._test_thread.terminate()
        self._tested = True

    @QtCore.pyqtSlot(int)
    @QtCore.pyqtSlot(str)
    def _receive_emit_error(self, signal):
        if isinstance(signal, int):
            self.error.emit("Received signal: {}".format(signal))
        else:
            self.error.emit(signal)

    @QtCore.pyqtSlot(int)
    def _emit_progress(self, progress):
        #passthrough progress status:
        debug("got progress signal: %s", progress)
        self.progress.emit(progress)

    @QtCore.pyqtSlot(str)
    def _recieve_status(self, msg):
        #recieve and store status messages:
        debug("got status signal: %s", msg)
        self.message.emit("Thread reports: {}".format(msg))

    @QtCore.pyqtSlot(str)
    def _recieve_error(self, msg):
        #recieve and process error messages:
        debug("got error signal: %s", msg)
        self._demux.finished.disconnect(self._launch_remux_thread)
        self.error.emit("Error: {}".format(msg))
        self.exit_thread()

    @QtCore.pyqtSlot(int)
    def _recieve_returncode(self, code):
        debug("got returncode signal: %s", code)
        self.returncode.emit(code)

    @QtCore.pyqtSlot()
    def exit_thread(self):
        #when the signal is recieved launch the function
        #that stops the current_job thread:
        self._tag_thread.terminate()

        #disconnect all signals and delete objects:
        self._tag_thread.disconnect()

        #emit all finalizing messages:
        self.progress.emit(100)
        self.error.emit("Interrupted")
        self.finished.emit()

    def _start_tagging(self):
        self.delete(self._m4b_file)

        self._tag_thread = Tagger(self._bin_path)
        self._tag_thread.finished.connect(self._finish_cleanup)
        self._tag_thread.progress.connect(self._emit_progress)
        self._tag_thread.status.connect(self._recieve_status)
        self._tag_thread.error.connect(self._recieve_error)
        self._tag_thread.returncode.connect(self._recieve_returncode)

        self._tag_thread.tag(self._cmd)

    @QtCore.pyqtSlot()
    def _finish_cleanup(self):
        self.delete(self._m4b_temp_file)
        self._tag_thread.disconnect()
        self.message.emit("Finished tagging file...")
        self.finished.emit()

    def tag(self, data):
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")

        #setup paths and file names for files:
        self._file_path, self._file_name = os.path.split(data["file"])
        self._file_name = os.path.splitext(self._file_name)[0]

        self._m4b_temp_file = r"{}_temp.m4b".format(os.path.join(self._file_path, self._file_name))
        self._m4b_file = r"{}.m4b".format(os.path.join(self._file_path, self._file_name))

        #create cmd for subprocess from dict:
        self._cmd.append(self._m4b_temp_file)

        self._cmd.append("--artist")
        self._cmd.append(data["artist"])

        self._cmd.append("--albumArtist")
        self._cmd.append(data["album artist"])

        self._cmd.append("--title")
        self._cmd.append(data["title"])

        self._cmd.append("--sortOrder")
        self._cmd.append("name")
        self._cmd.append(data["sort title"])

        self._cmd.append("--album")
        self._cmd.append(data["album"])

        self._cmd.append("--tracknum")
        self._cmd.append("{}/{}".format(data["track no"], data["tot tracks"]))

        self._cmd.append("--disk")
        self._cmd.append(str(data["disk no"]))

        self._cmd.append("--year")
        self._cmd.append(data["date"])

        self._cmd.append("--copyright")
        self._cmd.append(data["copyright"])
        self._cmd.append("--ISO-copyright")
        self._cmd.append(data["copyright"])

        self._cmd.append("--description")
        self._cmd.append(data["description"])
        self._cmd.append("--longdesc")
        self._cmd.append(data["description"])
        self._cmd.append("--storedesc")
        self._cmd.append(data["description"])

        try:
            cover = data["cover"]
            if cover is not None:
                self._cmd.append("--artwork")
                self._cmd.append(cover)
        except KeyError:
            pass

        self._cmd.append("--genre")
        self._cmd.append("Audiobooks")
        self._cmd.append("--stik")
        self._cmd.append("Audiobook")

        self._cmd.append("--comment")
        self._cmd.append("")
        self._cmd.append("--composer")
        self._cmd.append("")

        self._cmd.append("--purchaseDate")
        self._cmd.append("timestamp")

        self._cmd.append("--encodingTool")
        self._cmd.append("")
        self._cmd.append("--encodedBy")
        self._cmd.append("")

        self._cmd.append("--output")
        self._cmd.append(self._m4b_file)

        debug("complete _cmd for tagging: %s", self._cmd)

        self._start_tagging()
