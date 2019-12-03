#!/usr/bin/env python3

import logging
import ffmpeg
import os
from getopt import getopt, GetoptError
import subprocess
import sys

from pathlib import Path
from os import getenv
from shutil import which

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

if logging.getLogger().getEffectiveLevel() <= logging.INFO:
    ffmpeg_verbose = True
else:
    ffmpeg_verbose = False


# Get 'netmdcli' path from either environment variable or search
if getenv('NETMDCLI'):
    netmdcli = Path(getenv('NETMDCLI'))
else:
    if which('netmdcli') is not None:
        netmdcli = Path(which('netmdcli'))
    else:
        raise (FileNotFoundError, 'NetMD tools cannot be found; set environment variable NETMDCLI or'
                                  ' check install.')

logging.info("NETMDCLI: Using netmdcli at path: " + str(netmdcli))

if __name__ == "__main__":
    # Parse command-line arguments, set conversion path
    try:
        opts, args = getopt(sys.argv[1:], 'd:f:h', ['dir=', 'file='])
    except GetoptError:
        sys.exit(2)

    conv_dir = None
    tempdir = None

    for opt, arg in opts:
        if opt in ('-d', '--dir'):
            conv_path = arg
        elif opt in ('-f', '--file'):
            infile = arg
        elif opt in ('-t', '--tempdir'):
            tempdir = arg

    if tempdir is None:
        tempdir = "/tmp"

    outfile = Path(tempdir, 'netmd_temp.wav')

    try:
        conv_file = ffmpeg.input(filename=infile)
        conv_file = ffmpeg.output(conv_file, str(outfile))
        conv_file = ffmpeg.overwrite_output(conv_file)
        logging.info("Converting " + str(infile))
        ffmpeg.run(conv_file, quiet=ffmpeg_verbose)

        logging.info("Copying " + str(infile + " to NetMD..."))
        subprocess.run(str(netmdcli) + " send " + str(outfile), shell=True)
    except FileNotFoundError as err:
        raise FileNotFoundError
