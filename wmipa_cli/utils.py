import os
import sys

from wmipa_cli.log import logger


def check_os_version(sysname=None, machine=None):
    sysinfo = os.uname()
    if sysname is not None and sysinfo.sysname != sysname:
        return False
    if machine is not None and sysinfo.machine != machine:
        return False
    return True


def check_python_version():
    return sys.version_info[0] == 3 and sys.version_info[1] == 8


def safe_cmd(command):
    res = os.system(command)
    if res != 0:
        logger.error(f"Error while executing {command}.")
        sys.exit(1)


def remove_suffix(s, suffix):
    if s.endswith(suffix):
        return s[:-len(suffix)]
    return s
