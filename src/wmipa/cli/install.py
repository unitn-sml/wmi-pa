import argparse
import os
import sys

from wmipa.cli.installers.installer import Installer
from wmipa.cli.installers.latte import LatteInstaller
from wmipa.cli.log import logger
from wmipa.cli.utils import get_default_include_lib_paths, safe_cmd


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add arguments to the parser for the 'install' command.
    """
    parser.add_argument("--msat", help="Install MathSAT", action="store_true")
    parser.add_argument(
        "--nra", help="Install PySMT version with NRA support", action="store_true"
    )
    parser.add_argument("--latte", help="Install LattE Integrale", action="store_true")
    parser.add_argument("--all", help="Install all dependencies", action="store_true")
    parser.add_argument(
        "--install-path",
        help="Install path for external tools",
        default=f"{os.path.expanduser('~')}/.wmipa",
        type=str,
    )
    parser.add_argument(
        "--assume-yes", "-y", help="Automatic yes to prompts", action="store_true"
    )
    parser.add_argument(
        "--force-reinstall",
        "-f",
        help="Force reinstallation of dependencies",
        action="store_true",
    )

    default_include, default_lib = get_default_include_lib_paths()

    parser.add_argument(
        "--include-path",
        help="Additional include paths for compilation (can be specified multiple times)",
        action="append",
        dest="include_path",
        default=default_include,
    )
    parser.add_argument(
        "--lib-path",
        help="Additional library paths for compilation (can be specified multiple times)",
        action="append",
        dest="lib_path",
        default=default_lib,
    )
    parser.add_argument("--cxx", help="C++ compiler to use", default="g++", type=str)


def _msat_set_paths(env, include_paths: list[str], lib_paths: list[str]) -> None:
    if include_paths:
        c_include_paths = env.get("C_INCLUDE_PATH", "").split(":") + include_paths
        env["C_INCLUDE_PATH"] = ":".join(c_include_paths)
    if lib_paths:
        c_lib_paths = env.get("LIBRARY_PATH", "").split(":") + lib_paths
        env["LIBRARY_PATH"] = ":".join(c_lib_paths)


def install_msat(
    force_reinstall: bool,
    include_paths: list[str],
    lib_paths: list[str],
    assume_yes: bool = False,
) -> None:
    logger.info("Installing MathSAT via pysmt-install...")
    env = os.environ.copy()
    _msat_set_paths(env, include_paths, lib_paths)
    cmd = ["pysmt-install", "--msat"]
    if assume_yes:
        cmd.append("--confirm-agreement")
    if force_reinstall:
        cmd.append("--force")
    safe_cmd(cmd, env=env)


def install_pysmt_nra(
    force_reinstall: bool, include_paths: list[str], lib_paths: list[str]
) -> None:
    url = "git+https://git@github.com/masinag/pysmt@nrat#egg=pysmt"
    logger.info(f"Installing PySMT with NRA support from {url}...")
    env = os.environ.copy()
    _msat_set_paths(env, include_paths, lib_paths)
    cmd = [sys.executable, "-m", "pip", "install", url]
    if force_reinstall:
        cmd.append("--force-reinstall")
    safe_cmd(cmd, env=env)


def run(args: argparse.Namespace) -> None:
    if not any((args.all, args.latte, args.msat, args.nra)):
        print("Nothing to do. Use --help for more information.")
        return

    if args.all or args.nra:
        install_pysmt_nra(args.force_reinstall, args.include_path, args.lib_path)
    elif args.msat:
        install_msat(args.force_reinstall, args.include_path, args.lib_path)
        print("MathSAT installed successfully. You can now use it with PySMT.")

    installers: list[Installer] = []

    if args.all or args.latte:
        installers.append(
            LatteInstaller(
                args.install_path, args.include_path, args.lib_path, args.cxx
            )
        )
    for installer in installers:
        print(f"Installing {installer.get_name()}...")
        installer.install(args.assume_yes, args.force_reinstall)
        print(f"{installer.get_name()} installed successfully.")
    paths_to_export = []
    for installer in installers:
        paths_to_export.extend(installer.paths_to_export)
    if paths_to_export:
        logger.info("")
        logger.info("Add the following lines to your ~/.bashrc file:")
        for path in paths_to_export:
            logger.info(f"export PATH={path}:$PATH")
        logger.info("")
        logger.info("Then run: source ~/.bashrc")
    print(
        "Installation complete. You can now use wmipa with the installed dependencies."
    )
