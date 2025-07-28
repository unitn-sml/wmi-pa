import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from wmipa_cli.log import logger


def check_os_version(sysname=None, machine=None):
    sysinfo = os.uname()
    if sysname is not None and sysinfo.sysname != sysname:
        return False
    if machine is not None and sysinfo.machine != machine:
        return False
    return True


def safe_cmd(
    command: list[str],
    shell: bool = False,
    cwd: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
) -> str:
    """Safe command execution with proper error handling.
    Args:
        command (str | Collection[str]): Command to execute, can be a string or a list
        shell (bool): Whether to execute the command in a shell
        cwd (str | None): Current working directory to execute the command in
        env (dict[str, str] | None): Environment variables to set for the command
    Returns:
        str: The standard output of the command
    Raises:
        FileNotFoundError: If the command is not found
        Exception: If any other error occurs during command execution
    """
    try:
        logger.info(
            f"Executing: {' '.join(command) if isinstance(command, list) else command}"
        )

        result = subprocess.run(
            command, shell=shell, capture_output=True, text=True, cwd=cwd, env=env
        )

        if result.returncode != 0:
            logger.error(f"Command failed with return code {result.returncode}")
            logger.error(
                f"Command: {' '.join(command) if isinstance(command, list) else command}"
            )
            logger.error(f"Stdout: {result.stdout}")
            logger.error(f"Stderr: {result.stderr}")
            raise RuntimeError(
                f"Command failed with return code {result.returncode}. "
                f"See logs for details."
            )

        return result.stdout

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Command not found: {command}. Please ensure it is installed and available in your PATH."
        ) from e
    except Exception as e:
        raise Exception(
            f"An error occurred while executing the command: {command}. Error: {str(e)}"
        ) from e


def remove_suffix(s: str, suffix: str) -> str:
    """Remove the specified suffix from the string if it exists.
    Args:
        s (str): The string to process.
        suffix (str): The suffix to remove.
    Returns:
        str: The string with the suffix removed, or the original string if the suffix was not present.
    """
    if s.endswith(suffix):
        return s[: -len(suffix)]
    return s


def get_default_include_lib_paths() -> tuple[list[str], list[str]]:
    """Get Homebrew paths for macOS"""
    include_paths, lib_paths = [], []

    if sys.platform != "darwin":
        return include_paths, lib_paths

    for prefix in ["/opt/homebrew", "/usr/local"]:
        if Path(prefix).exists():
            include_path = os.path.join(prefix, "include")
            lib_path = os.path.join(prefix, "lib")
            include_paths.append(include_path)
            lib_paths.append(lib_path)
    return include_paths, lib_paths
