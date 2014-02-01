#!/usr/bin/env/python3
# -*- coding: utf-8 -*-

import logging
import inspect

class Log:
    logger = logging.getLogger(__name__)
    debug, warn, error = range(3)
    
    def __init__(self, debug=False):
        
        if debug:
            self.logger.setLevel(logging.DEBUG)
            log_format = "{lineno}: {rfuncName}, {module}.py, {levelname}: {message}"
        else:
            self.logger.setLevel(logging.ERROR)
            log_format = "{levelname}: {message}"
        stream = logging.StreamHandler()
        log_format = logging.Formatter(log_format, style='{')
        stream.setFormatter(log_format)
        self.logger.addHandler(stream)

    def __call__(self, *args, log=0):
        func_name = inspect.getframeinfo(inspect.currentframe().f_back)[2]
        if log == 0:
            self.logger.debug(*args, extra={'rfuncName': func_name})
        elif log == 1:
            self.logger.warn(*args, extra={'rfuncName': func_name})
        elif log == 2:
            self.logger.error(*args, extra={'rfuncName': func_name})

l=Log(True)
l("dddd")
def f():
    l("ffff")
    l("rrr", 1)
    l("hhhh", 2)
f()