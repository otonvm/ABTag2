#!/usr/bin/env/python3
# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import logging
import urllib.error
import urllib.request

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("Unable to import BeautifulSoup") from None

try:
    import html5lib # used by bs, not needed directly
except ImportError:
    raise ImportError("Unable to import html5lib") from None
del html5lib

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


class HTTPException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg


class URLException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg


class BS4Exception(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg


class RegExException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg


class Metadata:
    def __init__(self):
        self._url = None
        self._html = None
        self._soup = None
        self._title = None
        self._title_raw = None
        self._author = None
        self._author_span = None
        self._narrator_span = None
        self._narrator = None
        self._series_tuple = None
        self._runtime = None
        self._runtime_sec = None
        self._date_span = None
        self._date_obj = time.struct_time
        self._date = None
        self._content_div = None
        self._content_div_list = None
        self._description = None
        self._copyright = None

    def _load_html(self, path):
        if os.path.isfile(path):
            self._html = Tools.load_pickle(path)
            return

        if os.path.isdir(path):
            html_dump = os.path.join(path, "page.pkl")
            if os.path.exists(html_dump):
                self._html = Tools.load_pickle(html_dump)
                return

    def _http_download(self, url, path=None):
        try:
            self._html = urllib.request.urlopen(url).read()

        except urllib.error.HTTPError as err:
            raise HTTPException("the server couldn't fulfill the request, \
                                reason: {}".format(err.code)) from None

        except urllib.error.URLError as err:
            raise URLException("failed to reach server, reason: {}".format(err.reason)) from None

        else:
            if path is not None:
                if os.path.isdir(path):
                    html_dump = os.path.join(path, "page.pkl")
                    Tools.dump_pickle(html_dump, self._html)
                    return True

                else:
                    raise ValueError("path must be a folder") from None
            else:
                return True

    @staticmethod
    def is_url_valid(url):
        return url.startswith("http://www.audible.com/pd/") or \
            url.startswith("http://www.audible.co.uk/pd/")

    def http_page(self, url, path=None):
        """
        Method that downloads all contents from a web page.

        url:    has to start with "http://www.audible.com/pd/"
        path:   optional path to save and load backups of data,
                it can be a file or folder
        """
        if self.is_url_valid(url):
            #no soup object exists:
            if self._soup is None:
                #a path was provided and loading from pickle worked:
                if path is not None and self._load_html(path):
                    return True
                else:
                    #no data available so it has to be downloaded
                    #if path is provided a backup will be done:
                    self._http_download(url, path)
                #parse the html:
                self._create_soup()
                print("<----------------->")

        else:
            raise lib_exceptions.URLException("{} provided is invalid. \
                                           It has to be in the form of http://www.audible.com/pd/*")
