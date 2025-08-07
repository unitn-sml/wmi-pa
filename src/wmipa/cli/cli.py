import argparse

from wmipa.cli import install, run
from wmipa.cli.log import logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WMI-PA CLI: A command-line interface for WMI-PA.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run '%(prog)s command --help' for more information on a specific command.",
    )

    subparsers = parser.add_subparsers(
        dest="command", help="WMI-PA command", required=True
    )

    install_parser = subparsers.add_parser(
        "install", help="Install dependencies for WMI-PA CLI"
    )
    install.add_arguments(install_parser)
    run_parser = subparsers.add_parser("run", help="Run WMI-PA on a given Density file")
    run.add_arguments(run_parser)

    return parser.parse_args()


def cli():
    args = parse_args()

    if args.command == "install":
        install.run(args)
    elif args.command == "run":
        run.run(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1
    print("Command executed successfully.")

    return 0
