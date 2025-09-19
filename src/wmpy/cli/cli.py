import argparse

from wmpy.cli import install, run
from wmpy.cli.log import logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WM*PY CLI: A command-line interface for WM*PY.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run '%(prog)s command --help' for more information on a specific command.",
    )

    subparsers = parser.add_subparsers(
        dest="command", help="WM*PY command", required=True
    )

    install_parser = subparsers.add_parser(
        "install",
        help="Install dependencies for WM*PY CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    install.add_arguments(install_parser)
    run_parser = subparsers.add_parser(
        "run",
        help="Run WM*PY on a given Density file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    run.add_arguments(run_parser)

    return parser.parse_args()


def cli() -> int:
    args = parse_args()

    if args.command == "install":
        install.run(args)
    elif args.command == "run":
        run.run(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1

    return 0
