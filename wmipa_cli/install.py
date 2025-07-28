import argparse
import os
import sys

from wmipa_cli.installers.latte import LatteInstaller
from wmipa_cli.installers.volesti import VolestiInstaller
from wmipa_cli.log import logger
from wmipa_cli.utils import safe_cmd


def run() -> None:
    args = parse_args(sys.argv[1:])
    if not any((args.all, args.latte, args.volesti, args.msat, args.nra)):
        print("Nothing to do. Use --help for more information.")
        return

    if args.all or args.nra:
        install_pysmt_nra(args.force_reinstall, args.include_path, args.lib_path)
    elif args.msat:
        install_msat(args.force_reinstall, args.include_path, args.lib_path)

    installers = []

    if args.all or args.latte:
        installers.append(
            LatteInstaller(
                args.install_path, args.include_path, args.lib_path, args.cxx
            )
        )
    if args.all or args.volesti:
        installers.append(
            VolestiInstaller(args.install_path, args.include_path, args.lib_path)
        )
    for installer in installers:
        installer.install(args.assume_yes, args.force_reinstall)
    paths_to_export = []
    for installer in installers:
        paths_to_export.extend(installer.paths_to_export)
    if paths_to_export:
        print()
        print("Add the following lines to your ~/.bashrc file:")
        for path in paths_to_export:
            print(f"export PATH={path}:$PATH")
        print()
        print("Then run: source ~/.bashrc")


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--msat", help="Install MathSAT", action="store_true")
    parser.add_argument(
        "--nra", help="Install PySMT version with NRA support", action="store_true"
    )
    parser.add_argument("--latte", help="Install LattE Integrale", action="store_true")
    parser.add_argument("--volesti", help="Install Volesti", action="store_true")
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

    parser.add_argument(
        "--include-path",
        help="Additional include paths for compilation (can be specified multiple times)",
        action="append",
        dest="include_path",
    )
    parser.add_argument(
        "--lib-path",
        help="Additional library paths for compilation (can be specified multiple times)",
        action="append",
        dest="lib_path",
    )
    parser.add_argument(
        "--cxx", help="C++ compiler to use (default: g++)", default="g++", type=str
    )

    args = parser.parse_args(args)
    if args.include_path is None:
        args.include_path = []
    if args.lib_path is None:
        args.lib_path = []

    return args


def _msat_set_paths(env, include_paths: list[str], lib_paths: list[str]) -> None:
    if include_paths:
        c_include_paths = env.get("C_INCLUDE_PATH", "").split(":") + include_paths
        env["C_INCLUDE_PATH"] = ":".join(c_include_paths)
    if lib_paths:
        c_lib_paths = env.get("LIBRARY_PATH", "").split(":") + lib_paths
        env["LIBRARY_PATH"] = ":".join(c_lib_paths)


def install_msat(
    force_reinstall: bool, include_paths: list[str], lib_paths: list[str]
) -> None:
    logger.info("Installing MathSAT via pysmt-install...")
    env = os.environ.copy()
    _msat_set_paths(env, include_paths, lib_paths)
    cmd = ["pysmt-install", "--msat", "--confirm-agreement"]
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
