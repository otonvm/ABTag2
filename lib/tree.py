#!/usr/bin/env/python3
# -*- coding: utf-8 -*-

import os
import logging
from lib.util import Tools

DEBUG = True

#logging is enabled only for debugging
logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)
    log_format = "%(lineno)d: %(funcName)s, %(module)s.py, %(levelname)s: %(message)s"
    fmt = logging.Formatter(log_format, datefmt="%d/%m-%H:%M")
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
else:
    stream = logging.NullHandler()
logger.addHandler(stream)
debug = logger.debug


class Parse:
    """
    Helper class for parsing a folder tree and getting out specific items.
    The tree_ in the name is there to help distinguish members of this class.

    The class must be initialized with a path to a folder to parse.

    audio_files:    property that returns a list of paths to just audio files
    cover:          property that returns the path to a cover image
    xml:            property that returns the path to a xml file
    all_files:      property that returns a list of all valid files found

    """

    def __init__(self, folder):
        if not isinstance(folder, str):
            raise ValueError("folder must be a string")
        else:
            self._folder = folder
    
        debug("_folder: %s", self._folder)

        self._file_list = None
        self._audio_files = None
        self.audio_extensions = [".m4a"]
        self._cover = None
        self.cover_extensions = [".png", ".jpg", ".jpeg"]
        self._xml = None

        self._parse()

    def _glob_folder(self):
        self._file_list = []
        try:
            for file in os.listdir(self._folder):
                self._file_list.append(os.path.join(self._folder, file))
            debug("_file_list: %s", self._file_list)

        except FileNotFoundError:
            raise FileNotFoundError("{} not found".format(self._folder)) from None
        return

    def _get_audio_files(self):
        #create a new list of audio files if their extension is in a predefined list:
        self._audio_files = [file for file in self._file_list
                             if os.path.splitext(file)[1] in self.audio_extensions]
        debug("_audio_files: %s", self._audio_files)

    def _get_cover(self):
        #create a new list with all images:
        cover = [file for file in self._file_list
                 if os.path.splitext(file)[1] in self.cover_extensions]
        debug("cover: %s", cover)

        #pick only the first image if there are more then one:
        if len(cover) > 1:
            self._cover = cover[0]
        else:
            try:
                self._cover = cover[0]
            except IndexError:
                self._cover = None
        debug("_cover: %s", self._cover)

    def _get_xml(self):
        #create a new list with all xml files:
        xml_files = [os.path.abspath(file) for file in self._file_list
                     if os.path.splitext(file)[1] == ".xml"]
        debug("xml_files: %s", xml_files)

        if len(xml_files) > 1:
            self._xml = xml_files[0]
        else:
            try:
                self._xml = xml_files[0]
            except IndexError:
                self._xml = None
        debug("_xml: %s", self._xml)

    def _parse(self):
        #get folder contents:
        self._glob_folder()
        #sort the list of files alphabetically:
        self._file_list.sort()

    @property
    def audio_files(self):
        self._get_audio_files()
        return self._audio_files

    @property
    def cover(self):
        self._get_cover()
        return self._cover

    @property
    def xml(self):
        self._get_xml()
        return self._xml

    @property
    def all_files(self):
        all_files = []
        for file in self.audio_files:
            all_files.append(file)
        if self.cover is not None:
            all_files.append(self.cover)
        if self.xml is not None:
            all_files.append(self.xml)
        debug("all_files: %s", all_files)
        return all_files