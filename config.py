#!/usr/bin/env/python3
# [SublimeLinter flake8-ignore:+E301]
# -*- coding: utf-8 -*-


class Config:
    def __init__(self):
        self._verbose = False
        self._input_folder = None
        self._mp4box = ""
        self._atomicparsley = ""
        self._cover = None
        self._audio_files = []
        self._url = None
        self._title = None
        self._authors = None
        self._narrators = None
        self._series_title = None
        self._series_no = None
        self._date = None
        self._description = None
        self._copyright = None

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
    def mp4box(self):
        return self._mp4box
    @mp4box.setter
    def mp4box(self, value):
        self._mp4box = value

    @property
    def atomicparsley(self):
        return self._atomicparsley
    @atomicparsley.setter
    def atomicparsley(self, value):
        self._atomicparsley = value

    @property
    def cover(self):
        return self._cover
    @cover.setter
    def cover(self, value):
        self._cover = value

    @property
    def audio_files(self):
        return self._audio_files
    @audio_files.setter
    def audio_files(self, val):
        if isinstance(val, list):
            self._audio_files.clear()
            self._audio_files.extend(val)
        else:
            self._audio_files.append(val)

    @property
    def url(self):
        return self._url
    @url.setter
    def url(self, value):
        self._url = value

    @property
    def title(self):
        return self._title
    @property
    def title_sort(self):
        if self._title.startswith("The"):
            return "{}, {}".format(self.title[4:], "The")
        else:
            return self._title
    @title.setter
    def title(self, val):
        self._title = val

    def title_full(self, track=0):
        if self.series_no > 0:
            if len(self.audio_files) > 1:
                return "Book {}: {}, Part {}".format(self.series_no,
                                                     self.title, track)
            else:
                return "Book {}: {}".format(self.series_no,
                                            self.title)
        else:
            return self.title

    @property
    def authors(self):
        return self._authors
    @property
    def authors_string(self):
        if self._authors is not None:
            return ', '.join(self._authors)
        else:
            return self._authors
    @authors.setter
    def authors(self, val):
        self._authors = []
        if isinstance(val, list):
            self._authors.clear()
            self._authors.extend(val)
        else:
            self._authors.append(val)

    @property
    def narrators(self):
        return self._narrators
    @property
    def narrators_string(self):
        if self._narrators is not None:
            return ', '.join(self._narrators)
        else:
            return self._narrators
    @narrators.setter
    def narrators(self, val):
        self._narrators = []
        if isinstance(val, list):
            self._narrators.clear()
            self._narrators.extend(val)
        else:
            self._narrators.append(val)

    @property
    def series_title(self):
        return self._series_title
    @series_title.setter
    def series_title(self, val):
        self._series_title = val

    @property
    def series_no(self):
        return self._series_no
    @series_no.setter
    def series_no(self, val):
        if isinstance(val, int):
            self._series_no = val
        else:
            try:
                self._series_no = int(val)
            except ValueError:
                self._series_no = 0

    @property
    def date(self):
        return self._date
    @date.setter
    def date(self, val):
        self._date = val

    @property
    def description(self):
        return self._description
    @description.setter
    def description(self, val):
        self._description = val

    @property
    def copyright(self):
        return self._copyright
    @copyright.setter
    def copyright(self, val):
        self._copyright = val
