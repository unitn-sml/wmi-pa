import os
from abc import ABCMeta, abstractmethod

from wmipa_cli.log import logger


class Installer(metaclass=ABCMeta):
    def __init__(
        self, install_path: str, include_paths: list[str], lib_paths: list[str]
    ) -> None:
        self.install_path = os.path.abspath(install_path)
        self.include_paths = include_paths
        self.lib_paths = lib_paths
        self.paths_to_export: list[str] = []

    def install(self, yes: bool = False, force: bool = False) -> None:
        if not self.check_environment(yes):
            logger.error("Installation aborted.")
            return
        logger.info(f"Installing {self.get_name()} in {self.install_path}...")
        here = os.path.abspath(os.path.dirname(__file__))
        os.makedirs(os.path.join(here, self.install_path), exist_ok=True)
        os.chdir(self.install_path)
        self.download()
        self.unpack()
        self.build(force)
        self.add_to_path()
        os.chdir(here)

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
