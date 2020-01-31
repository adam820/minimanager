from pathlib import Path
from os import getenv
from shutil import which


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