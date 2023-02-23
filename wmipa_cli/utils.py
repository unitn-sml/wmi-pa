import os
import sys


def check_os_version(sysname=None, machine=None):
    sysinfo = os.uname()
    if sysname is not None and sysinfo.sysname != sysname:
        return False
    if machine is not None and sysinfo.machine != machine:
        return False
    return True


def check_python_version():
    return sys.version_info[0] == 3 and sys.version_info[1] == 8
