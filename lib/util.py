# -*- coding: utf-8 -*-

import os
import pickle
import logging

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


class Tools:
    _cache = {}

    def _abs_path(self, path):
        """This function creates a normalized version
        of the path that was used as the argument.
        It also uses a cache so all the conversions
        are done only once."""

        debug("current cache: %s", self._cache)

        #save path in argument
        arg_path = path
        try:
            #try to return whats in cache:
            debug("trying to access %s path in cache", arg_path)
            return self._cache[arg_path]
        except KeyError:
            debug("%s not found in cache", arg_path)
            #normalize path:
            path = os.path.expanduser(path)
            path = os.path.expandvars(path)
            path = os.path.normpath(path)
            #save the result in the cache:
            self._cache[arg_path] = path
            debug("stored %s in cache", self._cache[arg_path])
            return path

    def path_exists(self, path):
        debug("checking existance of path %s", path)

        path = self._abs_path(path)
        debug("absolute path: %s", path)

        exists = os.path.exists(path)
        if exists:
            return exists
        else:
            path = os.path.abspath(path)
            debug("path does not exist, defaulting to %s", path)
            return os.path.exists(path)

    def path_is_dir(self, path):
        if self.path_exists(path):
            return os.path.isdir(self._abs_path(path))
        else:
            raise OSError(100, "error locating", path)

    def path_is_file(self, path):
        if self.path_exists(path):
            return os.path.isfile(self._abs_path(path))
        else:
            raise OSError(100, "error locating", path)

    def real_path(self, path):
        return os.path.realpath(self._abs_path(path))

    @staticmethod
    def load_pickle(path):
        """Tries to load pickle data from path and returns
        whatever was loaded.
        If any exception is caught returns None."""
        try:
            debug("trying to load pickle data")
            with open(path, mode='rb') as file:
                debug("opened file %s for reading", path)
                return pickle.load(file, encoding='utf-8')
        except (pickle.UnpicklingError, OSError) as err:
            debug("error in pickling from %s, error: %s", path, err)
            return None

    @staticmethod
    def dump_pickle(path, obj):
        try:
            debug("trying to dump data to file")
            with open(path, mode='wb') as file:
                debug("opened %s for writing", path)
                pickle.dump(obj, file)
                return True
        except (pickle.PicklingError, OSError) as err:
            debug("error in pickling to %s, error: %s", path, err)
            return False
