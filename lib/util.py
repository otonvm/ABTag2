# -*- coding: utf-8 -*-
# [SublimeLinter flake8-ignore:+E261,+E262]

import os


class Tools:
    def __init__(self):
        self._cache = {}

    def _abs_path(self, path):
        """This function creates a normalized version
        of the path that was used as the argument.
        It also uses a cache so all the conversions
        are done only once."""

        #save path in argument
        arg_path = path
        try:
            #try to return whats in cache:
            return self._cache[arg_path]
        except KeyError:
            #normalize path:
            path = os.path.expanduser(path)
            path = os.path.expandvars(path)
            path = os.path.normpath(path)
            #save the result in the cache:
            self._cache[arg_path] = path
            return path

    def path_exists(self, path):
        path = self._abs_path(path)

        exists = os.path.exists(path)
        if exists:
            return exists
        else:
            path = os.path.abspath(path)
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
