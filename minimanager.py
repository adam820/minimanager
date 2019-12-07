#!/usr/bin/env python3

import logging
import subprocess
import sys

from getopt import getopt, GetoptError
from os import getenv, remove
from pathlib import Path
from shutil import which

def logging_init():
    if fl_debug:
        logging.basicConfig(level=logging.DEBUG,
                            format="%(levelname)s: %(message)s")
    elif fl_verbose:
        logging.basicConfig(level=logging.INFO,
                            format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING,
                            format="%(levelname)s: %(message)s")


def show_help():
    print("Usage:\n")
    print("-v/--verbose  Enable verbose messages")
    print("-f/--file     Convert a single file")
    print("-d/--dir      Convert a directory of files")
    print("-F/--format   Specify the audio format, 'wav' or 'atrac3'")
    print("-t/--tempdir  Specify temporary directory for holding on-the-fly WAV conversions")
    print("--debug       Show extra debugging information.")
    print("\n")
    sys.exit()


def find_netmdcli():
    # Get 'netmdcli' path from either environment variable or search
    if getenv('NETMDCLI'):
        bin = Path(getenv('NETMDCLI'))
    else:
        if which('netmdcli') is not None:
            bin = Path(which('netmdcli'))
        else:
            raise FileNotFoundError("NetMD tools cannot be found set "
                                    "environment variable NETMDCLI or check install.")
    logging.debug("NETMDCLI: Using netmdcli at path: " + str(bin))
    return bin


def find_atracdenc():
    # Get 'atracdenc' path from either environment variable or search
    if getenv('ATRACDENC'):
        bin = Path(getenv('ATRACDENC'))
    else:
        if which('atracdenc') is not None:
            bin = Path(which('atracdenc'))
        else:
            if encformat == 'atrac3':
                raise FileNotFoundError("Could not locate 'atracdenc' program for ATRAC3 encoding.")
    logging.debug("ATRACDENC: Using atracdenc at path: " + str(bin))
    return bin


def find_ffmpeg():
    # Get 'atracdenc' path from either environment variable or search
    if getenv('FFMPEG'):
        bin = Path(getenv('FFMPEG'))
    else:
        if which('ffmpeg') is not None:
            bin = Path(which('ffmpeg'))
        else:
            raise FileNotFoundError(
                "Could not locate 'ffmpeg' program for transcoding.")
    logging.debug("FFMPEG: Using ffmpeg at path: " + str(bin))
    return bin

if __name__ == "__main__":
    has_atracdenc = False
    has_netmdcli = False
    fl_verbose = False
    fl_debug = False
    indir = None
    tempdir = None
    infile = None
    encformat = 'wav'

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
            fl_verbose = True
        elif opt in ('--debug'):
            fl_debug = True
        else:
            show_help()

    # Do setup and pre-flight items
    logging_init()
    ffmpeg = find_ffmpeg()
    netmdcli = find_netmdcli()
    atracdenc = find_atracdenc()

    if encformat == 'wav' or 'atrac3':
        logging.info("Transcoding to intermidate format: " + encformat)
    else:
        logging.error("Invalid transcoding format, use 'wav' or 'atrac3'")
        show_help()

    # Check defaults/requirements
    if tempdir is None:
        tempdir = Path("/tmp")

    if encformat == 'atrac3':
        # To do ATRAC, it has to be encoded with 'atracdenc' first,
        # then wrapped in a .wav container with 'ffmpeg', then xferred
        # to the NetMD.
        wavfile = Path(tempdir, str(infile.stem + ".wav"))
        atracfile = Path(tempdir, str(infile.stem + ".oma"))
        atracwav = Path(tempdir, str(infile.stem + ".wav"))
        try:
            # Transcode MP3/XYZ into WAV
            logging.info("Transcoding WAV: " + str(infile) + " -> " + str(wavfile))
            transcode = subprocess.run([str(ffmpeg), '-y', '-i', str(infile), str(wavfile)], check=True,
                                       capture_output=True)
            if transcode.returncode == 0:
                logging.info("Transcoding ATRAC: " + str(wavfile) + " -> " + str(atracfile))
                try:
                    # Transcode WAV to ATRAC3
                    transatrac = subprocess.run([
                        str(atracdenc),
                        '-e', 'atrac3',
                        '-i', str(wavfile),
                        '-o', str(atracfile)],
                        check=True, capture_output=True
                    )
                    transatrac.check_returncode()
                except subprocess.CalledProcessError as transatrac_err:
                    remove(str(atracfile))
                    raise subprocess.CalledProcessError(transatrac_err.stdout.decode('UTF-8'))
                remove(str(wavfile))
                logging.info("Wrapping ATRAC: " + str(atracfile) + " -> " + str(atracwav))
                try:
                    # Wrap ATRAC3 in WAV container
                    transawav = subprocess.run([
                        str(ffmpeg),
                        '-i',str(atracfile),
                        '-c:a','copy',str(atracwav)],
                        check=True, capture_output=True
                    )
                    transawav.check_returncode()
                except subprocess.CalledProcessError as transawav_err:
                    remove(str(atracwav))
                    raise subprocess.CalledProcessError(transawav_err.stdout.decode('UTF-8'))
                remove(str(atracfile))
                logging.info("Sending " + str(wavfile) + " to NetMD...")
                try:
                    transmit = subprocess.run([str(netmdcli), 'send', str(atracwav)], check=True,
                                              capture_output=True)
                    transmit.check_returncode()
                    remove(str(atracwav))
                except subprocess.CalledProcessError as err:
                    logging.error(err.stdout.decode('UTF-8'))
                    remove(str(atracwav))
        except IOError as err:
            raise IOError(err)
    else:
        wavfile = Path(tempdir, str(infile.stem + ".wav"))
        try:
            logging.info("Transcoding: " + str(infile) + " -> " + str(wavfile))
            transcode = subprocess.run([str(ffmpeg), '-y', '-i', str(infile), str(wavfile)], check=True,
                                       capture_output=True)
            if transcode.returncode == 0:
                logging.info("Sending " + str(wavfile) + " to NetMD...")
                try:
                    transmit = subprocess.run([str(netmdcli), 'send', str(wavfile)], check=True,
                                              capture_output=True)
                    transmit.check_returncode()
                    remove(str(wavfile))
                except subprocess.CalledProcessError as err:
                    logging.error(err.stdout.decode('UTF-8'))
                    remove(str(wavfile))
        except IOError as err:
            raise IOError(err)
