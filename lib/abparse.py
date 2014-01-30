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

########    METHODS THAT DEAL WITH RAW DATA ####
    def _load_html(self, path):
        """Load cached html from a pickle file"""
        if os.path.isfile(path):
            debug("using %s for pickle data", path)

            self._html = Tools.load_pickle(path)

        elif os.path.isdir(path):
            html_dump = os.path.join(path, "page.pkl")
            debug("using %s for pickle data", html_dump)

            if os.path.exists(html_dump):
                self._html = Tools.load_pickle(html_dump)
        else:
            return False

        if self._html is not None:
            return True
        else:
            return False

    def _http_download(self, url, path=None):
        """Download html page and save downloaded file to pickle"""
        try:
            debug("downloading from url: %s", url)
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
                    debug("saving downloaded data to: %s", html_dump)
                    return Tools.dump_pickle(html_dump, self._html)

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

########    METHODS THAT CREATE THE SOUP    ####
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

########    METHODS THAT EXTRACT THE TITLE  ####
    def _set_title_raw(self):
        """Extract raw title data from soup"""
        self._title_raw = self._soup.find('h1', {'class': 'adbl-prod-h1-title'}).string.strip()
        debug("_title_raw: %s", self._title_raw)
        return

    def _set_title(self):
        """Parse raw title data and extract information"""
        if self._title_raw is None:
            self._set_title_raw()

        title_regex = re.search(r"^([\w\s']+)", self._title_raw)

        if title_regex:
            self._title = title_regex.group(1)
            return
        else:
            raise RegExException("could not extract title") from None

########    METHODS THAT EXTRACT AUTHORS    ####
    def _set_author_span(self):
        self._author_span = self._soup.find('li', {'class': 'adbl-author-row'})
        self._author_span = self._author_span.find('span', {'class': 'adbl-prod-author'})
        debug("_author_span: %s", self._author_span)
        return

    def _parse_author_span(self):
        if self._author_span is None:
            self._set_author_span()

        #get all text from div and create list (to remove \n etc.):
        author_span_list = self._author_span.text.strip().split(',')
        #strip unnecessary space from each string:
        author_span_list = [s.strip() for s in author_span_list]

        #join all data back into one string:
        self._author = ', '.join(author_span_list)
        return

    def _set_author(self):
        self._parse_author_span()
        return

########    METHODS THAT EXTRACT NARRATORS  ####
    def _set_narrator_span(self):
        self._narrator_span = self._soup.find('li', {'class': 'adbl-narrator-row'})
        self._narrator_span = self._narrator_span.find('span', {'class': 'adbl-prod-author'})
        debug("_narrator_span: %s", self._narrator_span)
        return

    def _parse_narrator_span(self):
        if self._narrator_span is None:
            self._set_narrator_span()

        #get all text from div and create list (to remove \n etc.):
        narrator_span_list = self._narrator_span.text.strip().split(',')
        #strip unnecessary space from each string:
        narrator_span_list = [s.strip() for s in narrator_span_list]

        #join all data back into one string:
        self._narrator = ', '.join(narrator_span_list)
        return

    def _set_narrator(self):
        self._parse_narrator_span()
        return

########    METHODS THAT EXTRAT SERIES DATA ####
    def _set_series_tuple(self):
        series = self._soup.find('div', {'class': 'adbl-series-link'})
        debug("series: %s", series)

        if series:
            series_name = series.a.string.strip()

            series_no = series.find('span', {'class': 'adbl-label'})
            series_no = series_no.string.strip()
            debug("series_no: %s", series_no)

            series_no_match = re.search(r'^,\s\S+\s(\d+)$', series_no)

            if series_no_match:
                series_no = series_no_match.group(1)
                self._series_tuple = (series_name, int(series_no))
                return
            else:
                raise RegExException("could not determine series position number")

        else:
            self._series_tuple = None
            return

    def _set_series_tuple_from_title(self):
        if self._title_raw is None:
            self._set_title_raw()

        exp = re.compile(r"^[\w\s]+:\s([\w\s']+),\sBook\s(\d)$")
        match = exp.match(self._title_raw)

        if match:
            series_title = match.group(1)
            series_no = int(match.group(2))

            self._series_tuple = (series_title, series_no)
            return
        else:
            self._series_tuple = None
            return

########    METHODS THAT EXTRAT RUNTIME DATA    ####
    def _set_runtime(self):
        runtime = self._soup.find('span', {'class': 'adbl-run-time'})
        self._runtime = runtime.string.strip()
        debug("_runtime: %s", self._runtime)
        return

    def _regex_runtime(self):
        if self._runtime is None:
            self._set_runtime()

        #match string like:
        #    23 hrs 45 mins
        #    15 hrs
        #returns an iterator of matches in sequence
        exp = re.compile(r'^(\d+)|\s(\d+)')
        match = re.findall(exp, self._runtime)

        #filter through tuples for actual results producing a list of either one or two entries:
        runtime_match_results = [l[0] or l[1] for l in match if l]
        debug("runtime_match_results: %s", runtime_match_results)

        if runtime_match_results:
            if len(runtime_match_results) == 1:  # only hrs
                hrs = int(runtime_match_results[0])

                self._runtime_sec = hrs * 60 * 60
                return
            elif len(runtime_match_results) == 2:  # both hrs and mins
                hrs = int(runtime_match_results[0])
                mins = int(runtime_match_results[1])

                self._runtime_sec = (hrs * 60 * 60) + (mins * 60)
                return
            else:
                raise RegExException("could not convert runtime string into secconds")
        else:
            raise RegExException("could not parse runtime string")

########    METHODS THAT EXTRACT RELEASE DATE DATA  ####
    def _set_date_span(self):
        self._date_span = self._soup.find('span', {"class": "adbl-date adbl-release-date"})
        debug("_date_span: %s", self._date_span)
        return

    def _set_date(self):
        if self._date_span is None:
            self._set_date_span()

        date_text = self._date_span.text.strip()
        self._date_obj = time.strptime(date_text, "%m-%d-%y")
        return

########    METHODS THAT EXTRACT THE DESCRIPTION    ####
    def _set_content_div(self):
        self._content_div = self._soup.find('div', {"class": "adbl-content"})
        debug("_content_div: %s", self._content_div)
        return

    def _parse_content_div(self):
        if self._content_div is None:
            self._set_content_div()

        #get all text from div and create list:
        content_div_list = self._content_div.text.strip().split('\n')
        #strip unnecessary space from each string:
        content_div_list = [s.strip() for s in content_div_list]
        #filter out all empty strings:
        content_div_list = [s for s in content_div_list if len(s) > 0]

        self._content_div_list = content_div_list
        debug("_content_div_list: %s", self._content_div_list)
        return

    def _set_description(self):
        if self._content_div_list is None:
            self._parse_content_div()
        self._description = ''.join([s for s in self._content_div_list if s[0] != '©'])
        return

    def _set_copyright(self):
        if self._content_div_list is None:
            self._parse_content_div()
        self._copyright = self._content_div_list[-1]
        debug("_copyright: %s", self._copyright)

        self._copyright = re.sub(r'\s\(P\)', '; Ⓟ', self._copyright)
        self._copyright = re.sub(r';;', ';', self._copyright)
        return

########    PUBLIC METHODS  ####
    @staticmethod
    def is_url_valid(url):
        """Simple check if the url provided looks valid"""
        return url.startswith("http://www.audible.com/pd/") or \
            url.startswith("http://www.audible.co.uk/pd/")

    def reset(self):
        """Reset html data and soup"""
        self._html = None
        self._soup = None
        return

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
                    pass
                else:
                    #no data available so it has to be downloaded
                    #if path is provided a backup will be done:
                    if self._http_download(url, path):
                        pass
                    else:
                        raise HTTPException("could not load html data from {}".format(path))
                #parse the html:
                self._create_soup()
            else:
                #nothing to do
                return

        else:
            raise URLException("{} provided is invalid. \
                                It has to be in the form of http://www.audible.com/pd/*")

    def local_html(self, html_file):
        """Load html from local file"""
        if not self._soup:
            self._local_file(html_file)
        return

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

    def series(self, try_title=False):
        if try_title:
            self._set_series_tuple_from_title()
        else:
            self._set_series_tuple()
        return self._series_tuple

    @property
    def runtime_string(self):
        self._set_runtime()
        return self._runtime

    @property
    def runtime_sec(self):
        self._regex_runtime()
        return self._runtime_sec

    @property
    def date_obj(self):
        self._set_date()
        return self._date_obj

    @property
    def date_utc(self):
        self._set_date()
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", self._date_obj)

    @property
    def description(self):
        self._set_description()
        return self._description

    @property
    def copyright(self):
        self._set_copyright()
        return self._copyright