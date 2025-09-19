import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from wmpy.cli.log import logger


def check_os_version(
    sysname: Optional[str] = None, machine: Optional[str] = None
) -> bool:
    sysinfo = os.uname()
    if sysname is not None and sysinfo.sysname != sysname:
        return False
    if machine is not None and sysinfo.machine != machine:
        return False
    return True


def safe_cmd(
    command: list[str],
    cwd: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
) -> str:
    """Safe command execution with proper error handling.
    Args:
        command: Command to execute as a list
        cwd: Current working directory to execute the command in
        env: Environment variables to set for the command
    Returns:
        str: The standard output of the command
    Raises:
        FileNotFoundError: If the command is not found
        RuntimeError: If the command fails
    """
    try:
        logger.info(
            f"Executing: {' '.join(command) if isinstance(command, list) else command}"
        )

        result = subprocess.run(command, shell=False, text=True, cwd=cwd, env=env)

        if result.returncode != 0:
            raise RuntimeError(
                f"Command {' '.join(command)} failed with return code {result.returncode}"
            )

        return result.stdout

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Command not found: {' '.join(command)}. Please ensure it is installed and available in your PATH."
        ) from e
    except Exception as e:
        raise Exception(
            f"An error occurred while executing the command: {command}. Error: {str(e)}"
        ) from e


def remove_suffix(s: str, suffix: str) -> str:
    """Remove the specified suffix from the string if it exists.
    Args:
        s: The string to process.
        suffix: The suffix to remove.
    Returns:
        str: The string with the suffix removed, or the original string if the suffix was not present.
    """
    if s.endswith(suffix):
        return s[: -len(suffix)]
    return s


def get_default_include_lib_paths() -> tuple[list[str], list[str]]:
    """Get Homebrew paths for macOS"""
    include_paths: list[str]
    lib_paths: list[str]
    include_paths, lib_paths = [], []

    if sys.platform.startswith("darwin"):
        for prefix in ["/opt/homebrew", "/usr/local"]:
            path = Path(prefix)
            if path.exists():
                include_path = path / "include"
                lib_path = path / "lib"
                include_paths.append(str(include_path))
                lib_paths.append(str(lib_path))
    return include_paths, lib_paths
