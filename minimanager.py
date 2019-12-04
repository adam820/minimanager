#!/usr/bin/env python3

import logging
import ffmpeg
from getopt import getopt, GetoptError
import subprocess
import sys

from pathlib import Path
from os import getenv
from shutil import which

def logging_init():
    if fl_verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

def show_help():
    print("Usage:\n")
    print("-v/--verbose  Enable verbose messages")
    print("-f/--file     Convert a single file")
    print("-d/--dir      Convert a directory of files")
    print("-t/--tempdir  Specify temporary directory for holding on-the-fly WAV conversions")
    print("\n")
    sys.exit()

def find_netmdcli():
    # Get 'netmdcli' path from either environment variable or search
    if getenv('NETMDCLI'):
        netmdcli = Path(getenv('NETMDCLI'))
    else:
        if which('netmdcli') is not None:
            netmdcli = Path(which('netmdcli'))
        else:
            raise FileNotFoundError("NetMD tools cannot be found set "
                "environment variable NETMDCLI or check install.")
    logging.info("NETMDCLI: Using netmdcli at path: " + str(netmdcli))

def find_atracdenc():
    # Get 'atracdenc' path from either environment variable or search
    if getenv('ATRACDENC'):
        atracdenc = Path(getenv('ATRACDENC'))
    else:
        if which('atracdenc') is not None:
            atracdenc = Path(which('atracdenc'))
        else:
            logging.warning("Could not locate 'atracdenc' program for ATRAC3 encoding.")
            return None
    logging.info("ATRACDENC: Using atracdenc at path: " + str(atracdenc))

if __name__ == "__main__":
    has_atracdenc = False
    has_netmdcli = False
    fl_verbose = False
    indir = None
    tempdir = None
    infile = None
    encformat = None
    
    # Parse command-line arguments, set conversion path
    try:
        opts, args = getopt(sys.argv[1:], 'd:f:F:t:hv', [
            'dir=', 'file=', 'tempdir=', 'format=', 'verbose', 'help'
        ])
        if len(opts) == 0:
            show_help()
    except GetoptError:
        sys.exit(1)

    for opt, arg in opts:
        if opt in ('-d', '--dir'):
            indir = Path(arg)
        elif opt in ('-f', '--file'):
            infile = Path(arg)
        elif opt in ('-t', '--tempdir'):
            tempdir = Path(arg)
        elif opt in ('-F', '--format'):
            encformat = str(arg)
        elif opt in ('-h', '--help'):
            show_help()
        elif opt in ('-v', '--verbose'):
            fl_verbose=True
        else:
            show_help()

    # Do setup and pre-flight items
    logging_init()
    find_netmdcli()
    find_atracdenc()

    if encformat == 'wav' or 'atrac3':
        logging.info("Transcoding to intermidate format: " + encformat)
    else:
        logging.error("Invalid transcoding format, use 'wav' or 'atrac3'")
        show_help()

    # Check defaults/requirements
    if tempdir is None:
        tempdir = Path("/tmp")

    outfile = Path(tempdir, str(infile.stem + ".wav"))
    print(str(outfile))
    # try:
    #     conv_file = ffmpeg.input(filename=infile)
    #     conv_file = ffmpeg.output(conv_file, str(outfile))
    #     conv_file = ffmpeg.overwrite_output(conv_file)
    #     logging.info("Converting " + str(infile))
    #     ffmpeg.run(conv_file, quiet=ffmpeg_verbose)

    #     logging.info("Copying " + str(infile) + "...")
    #     subprocess.run(str(netmdcli) + " send " + "\"" + str(outfile) + "\"",
    #                    shell=True)
    # except FileNotFoundError:
    #     raise FileNotFoundError
