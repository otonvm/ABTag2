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


class FileError(Exception):
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
        """Load cached html from a pickle file"""
        if os.path.isfile(path):
            self._html = Tools.load_pickle(path)
            return

        if os.path.isdir(path):
            html_dump = os.path.join(path, "page.pkl")
            if os.path.exists(html_dump):
                self._html = Tools.load_pickle(html_dump)
                return

    def _http_download(self, url, path=None):
        """Download html page and save downloaded file to pickle"""
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

    def _local_file(self, file_path):
        """Load html from local file"""
        try:
            with open(file_path, encoding='utf-8') as file:
                self._soup = BeautifulSoup(file, "html5lib")
                self._test_soup()
                return
        except FileExistsError:
            raise FileError("requested file inaccessible or already open") from None
        except OSError:
            raise FileError("could not open requested file") from None

    def _test_soup(self):
        """Test if the soup has a valid structure"""
        if self._soup.body is None or len(self._soup.body) == 0:
            raise BS4Exception("cannot parse document structure") from None
        return

    def _create_soup(self):
        """Create a soup object by parsing html data"""
        if self._html is not None:
            self._soup = BeautifulSoup(self._html, "html5lib")
            self._test_soup()
        return

    def _set_title_raw(self):
        """Extract raw title data from soup"""
        self._title_raw = self._soup.find('h1', {'class': 'adbl-prod-h1-title'}).string.strip()

    def _set_title(self):
        """Parse raw title data and extract information"""
        if self._title_raw is None:
            self._set_title_raw()

        title_regex = re.search(r"^([\w\s']+)", self._title_raw)

        if title_regex:
            self._title = title_regex.group(1)
        else:
            raise RegExException("could not extract title") from None

    def _set_author_span(self):
        self._author_span = self._soup.find('li', {'class': 'adbl-author-row'})
        self._author_span = self._author_span.find('span', {'class': 'adbl-prod-author'})

    def _parse_author_span(self):
        if self._author_span is None:
            self._set_author_span()

        #get all text from div and create list (to remove \n etc.):
        author_span_list = self._author_span.text.strip().split(',')
        #strip unnecessary space from each string:
        author_span_list = [s.strip() for s in author_span_list]

        #join all data back into one string:
        self._author = ', '.join(author_span_list)

    def _set_author(self):
        self._parse_author_span()

    def _set_narrator_span(self):
        self._narrator_span = self._soup.find('li', {'class': 'adbl-narrator-row'})
        self._narrator_span = self._narrator_span.find('span', {'class': 'adbl-prod-author'})

    def _parse_narrator_span(self):
        if self._narrator_span is None:
            self._set_narrator_span()

        #get all text from div and create list (to remove \n etc.):
        narrator_span_list = self._narrator_span.text.strip().split(',')
        #strip unnecessary space from each string:
        narrator_span_list = [s.strip() for s in narrator_span_list]

        #join all data back into one string:
        self._narrator = ', '.join(narrator_span_list)

    def _set_narrator(self):
        self._parse_narrator_span()

    @staticmethod
    def is_url_valid(url):
        """Simple check if the url provided looks valid"""
        return url.startswith("http://www.audible.com/pd/") or \
            url.startswith("http://www.audible.co.uk/pd/")

    def reset(self):
        """Reset html data and soup"""
        self._html = None
        self._soup = None

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
                    return
                else:
                    #no data available so it has to be downloaded
                    #if path is provided a backup will be done:
                    self._http_download(url, path)
                #parse the html:
                self._create_soup()

        else:
            raise URLException("{} provided is invalid. \
                                It has to be in the form of http://www.audible.com/pd/*")

    def local_html(self, html_file):
        """Load html from local file"""
        if not self._soup:
            self._local_file(html_file)

    @property
    def title(self):
        self._set_title()
        return self._title

    @property
    def title_raw(self):
        self._set_title()
        return self._title_raw

    @property
    def authors(self):
        self._set_author()
        return self._author

    @property
    def narrators(self):
        self._set_narrator()
        return self._narrator
