import os
from abc import ABCMeta, abstractmethod
from pathlib import Path

from wmpy.cli.log import logger


def expand_path(path_str: str) -> Path:
    """Expand environment variables and user home directory in path."""
    return Path(os.path.expandvars(os.path.expanduser(path_str))).resolve()

class Installer(metaclass=ABCMeta):
    def __init__(
        self, install_path: str, include_paths: list[str], lib_paths: list[str]
    ) -> None:
        self.install_path = expand_path(install_path)
        self.include_paths = include_paths
        self.lib_paths = lib_paths
        self.paths_to_export: list[str] = []

    def install(self, yes: bool = False, force: bool = False) -> None:
        if not self.check_environment(yes):
            logger.error("Installation aborted.")
            return

        logger.info(f"Installing {self.get_name()} in {self.install_path}...")
        self.install_path.mkdir(parents=True, exist_ok=True)

        original_cwd = Path.cwd()
        os.chdir(self.install_path)

        try:
            self.download()
            self.unpack()
            self.build(force)
            self.add_to_path()
        finally:
            os.chdir(original_cwd)

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass

    @abstractmethod
    def check_environment(self, yes: bool) -> bool:
        pass

    @abstractmethod
    def download(self) -> None:
        pass

    @abstractmethod
    def unpack(self) -> None:
        pass

    @abstractmethod
    def build(self, force: bool) -> None:
        pass

    @abstractmethod
    def add_to_path(self) -> None:
        pass
