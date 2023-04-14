import argparse
import os
import sys
import sysconfig
from logging import warning

from wmipa_cli.installers.latte import LatteInstaller
from wmipa_cli.installers.volesti import VolestiInstaller
from wmipa_cli.utils import check_os_version, check_python_version


def run():
    args = parse_args(sys.argv[1:])
    if args.all or args.msat_custom:
        install_msat_custom()
    installers = []

    if args.all or args.latte:
        installers.append(LatteInstaller(args.install_path))
    if args.all or args.volesti:
        installers.append(VolestiInstaller(args.install_path))
    for installer in installers:
        installer.install(args.y)
    paths_to_export = []
    for installer in installers:
        paths_to_export.extend(installer.paths_to_export)
    if paths_to_export:
        print()
        print("Add the following lines to your .bashrc file:")
        for path in paths_to_export:
            print(f"PATH={path}:$PATH")
        print()
        print("Then run: source ~/.bashrc")


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--msat-custom", help="Install MathSAT custom version for SA-PA-SK", action="store_true")
    parser.add_argument("--latte", help="Install LattE Integrale", action="store_true")
    parser.add_argument("--volesti", help="Install Volesti", action="store_true")
    parser.add_argument("--all", help="Install all dependencies", action="store_true")
    parser.add_argument("--install-path", help="Install path", default=f"{os.path.expanduser('~')}/.wmipa",
                        type=str)
    parser.add_argument("-y", help="Answer yes to all questions", action="store_true")
    return parser.parse_args(args)


def install_msat_custom():
    sysname, machine = "Linux", "x86_64"
    if not check_os_version(sysname, machine):
        warning(f"""The algorithm SA-WMI-PA-SK is supported only for {sysname} {machine}. 
    The installation will continue, but this algorithm will not work correctly.""")
        return
    if not check_python_version():
        warning("""The algorithm SA-WMI-PA-SK is supported only for Python 3.8.
    The installation will continue, but this algorithm will not work correctly.""")
        return
    install_msat()
    copy_custom_msat_binary()


def copy_custom_msat_binary():
    msat_install_dir = sysconfig.get_path("purelib")
    msat_so = "_mathsat.cpython-38-x86_64-linux-gnu.so"
    msat_py = "mathsat.py"
    url = "https://github.com/masinag/wmi-pa/raw/master/bin/{}"
    msat_so_url = url.format(msat_so)
    msat_py_url = url.format(msat_py)

    # download files to the venv/lib/python3.8/site-packages
    os.system(f"wget {msat_so_url} -O {os.path.join(msat_install_dir, msat_so)}")
    os.system(f"wget {msat_py_url} -O {os.path.join(msat_install_dir, msat_py)}")


def install_msat():
    os.system("pysmt-install --msat --confirm-agreement")
