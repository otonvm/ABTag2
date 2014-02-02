#!/usr/bin/env/python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from argparse import ArgumentParser

from PyQt5 import QtWidgets

from config import Config
from lib.util import Tools
from gui.resources import Icons
from gui.wizard import Wizard


DEBUG = True
VERSION = 0.1


logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)
    log_format = logging.Formatter("%(lineno)d: %(funcName)s, %(module)s.py, %(levelname)s: %(message)s")
else:
    logger.setLevel(logging.ERROR)
    log_format = logging.Formatter("%(levelname)s: %(message)s")
stream = logging.StreamHandler()
stream.setFormatter(log_format)
logger.addHandler(stream)
debug = logger.debug
error = logger.error
warn = logger.warning


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help="Display verbose information. [default: %(default)s]")

    parser.add_argument(dest='input_folder', metavar='<folder path>', action='store',
                        nargs='?', help="Input folder that contains all items.")

    parser.add_argument(dest='url', metavar='<url>', action='store', nargs='?',
                        help="url to audible page with metadata [default: None]")

    parser.add_argument('-c', '--cover', dest='input_cover', metavar='<cover image path>', action='store',
                        help="Path to a cover image. [default: None]")
    parser.add_argument('-V', '--version', action='version', version=str(VERSION))

    args = parser.parse_args()

    return args


def main():
    debug("argv: %s", sys.argv)
    debug("path: %s", sys.path)
    debug("current path: %s", os.getcwd())

    args = parse_args()
    debug("args: %s", args)

    config = Config()
    util = Tools()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        config.verbose = True

    script_path = util.real_path(os.path.split(__file__)[0])
    debug("script_path %s", script_path)

    debug("system: %s", platform.system())

    if platform.system() == "Windows":
        tools_path = os.path.join(script_path, "tools\win")
        config.mp4box = os.path.join(tools_path, "mp4box.exe")
        config.atomicparsley = os.path.join(tools_path, "AtomicParsley.exe")
    else:
        tools_path = os.path.join(script_path, "tools/mac")
        config.mp4box = os.path.join(tools_path, "mp4box")
        config.atomicparsley = os.path.join(tools_path, "AtomicParsley")
    debug("tools_path: %s", tools_path)
    debug("mp4box: %s", config.mp4box)
    debug("atomicparsley: %s", config.atomicparsley)

    if args.input_folder is not None:
        debug("checking %s", args.input_folder)

        try:
            if util.path_is_dir(args.input_folder):
                debug("%s is a directory", args.input_folder)
                config.input_folder = util.real_path(args.input_folder)

            else:
                warn("%s is not a folder", args.input_folder)
        except OSError as err:
            debug("error checking input_folder")
            raise SystemExit(err)

    if args.input_cover is not None:
        debug("checking %s", args.input_cover)

        try:
            if util.path_is_file(args.input_cover):
                debug("%s is a file", args.input_cover)
                config.input_cover = util.real_path(args.input_cover)

            else:
                warn("%s is not a file", args.input_cover)
        except OSError as err:
            debug("error checking input_cover")
            raise SystemExit(err)

    if args.url is not None:
        config.url = args.url

    debug("config after argparse: %s", config)

    #start gui:
    app = QtWidgets.QApplication([])
    Icons()
    wizard = Wizard(config)
    wizard.show()
    app.exec_()

if __name__ == "__main__":
    import platform

    if platform.system() == "Darwin":
        sys.argv.append("test_ab")
        sys.argv.append("http://www.audible.com/pd/Sci-Fi-Fantasy/On-Basilisk-Station-Audiobook/B002V1BOWY/ref=a_search_c4_1_1_srTtl?qid=1391030110&sr=1-1")
        #sys.argv.append("test_ab")
        pass
    else:
        #sys.argv.append("--help")
        #sys.argv.append(r"D:\Downloads\AAC Audiobooks")
        #sys.argv.append("--cover")
        #sys.argv.append(r"D:\Downloads\ImmPoster.jpg")
        sys.argv.append("test_ab")
        sys.argv.append("http://www.audible.com/pd/Sci-Fi-Fantasy/On-Basilisk-Station-Audiobook/B002V1BOWY")

        pass

    sys.exit(main())
