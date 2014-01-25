#!/usr/bin/env/python3
# [SublimeLinter flake8-ignore:+E301]
# -*- coding: utf-8 -*-


class Config:
    def __init__(self):
        self._verbose = False
        self._input_folder = None
        self._cover = None
        self._url = None

    def __str__(self):
        return str(self.__dict__)

    @property
    def verbose(self):
        return self._verbose
    @verbose.setter
    def verbose(self, value):
        self._verbose = value

    @property
    def input_folder(self):
        return self._input_folder
    @input_folder.setter
    def input_folder(self, value):
        self._input_folder = value

    @property
    def cover(self):
        return self._cover
    @cover.setter
    def cover(self, value):
        self._cover = value

    @property
    def url(self):
        return self._url
    @url.setter
    def url(self, value):
        self._url = value
