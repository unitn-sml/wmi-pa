import os

from wmpy.cli.installers.installer import Installer
from wmpy.cli.log import logger
from wmpy.cli.utils import check_os_version, safe_cmd


class VolestiInstaller(Installer):
    dependencies = ["cmake", "g++", "make"]

    def __init__(
        self, install_path: str, include_paths: list[str], lib_paths: list[str]
    ) -> None:
        super().__init__(install_path, include_paths, lib_paths)
        self.git_repo = "https://github.com/masinag/approximate-integration"

    @staticmethod
    def get_name() -> str:
        return "Volesti Integrator"

    @staticmethod
    def get_dir() -> str:
        return "approximate-integration"

    def check_environment(self, yes: bool) -> bool:
        logger.info(f"Checking environment for {self.get_name()}...")
        if not check_os_version("Linux"):
            logger.warning(
                f"""Automatic installation of {self.get_name()} is supported only for Linux.
        Please install it manually from {self.git_repo}"""
            )
            return False
        if not self.ask_dependencies_proceed(yes):
            return False
        return True

    def ask_dependencies_proceed(self, yes: bool) -> bool:
        logger.info("Make sure you have the following dependencies installed:")
        logger.info(" ".join(self.dependencies))
        logger.info("Do you want to proceed? [y/n] ")
        return yes or input().strip().lower() == "y"

    def download(self) -> None:
        if os.path.exists(self.get_dir()):
            logger.info(
                f"Skipping download of {self.get_name()}, directory approximate-integration already exists."
            )
            return
        logger.info(f"Downloading {self.get_name()}...")
        safe_cmd(["git", "clone", self.git_repo])

    def unpack(self) -> None:
        pass

    def build(self, force: bool) -> None:
        os.chdir(self.get_dir())
        if force:
            safe_cmd(["make", "clean"])
        safe_cmd(["make"])

    def add_to_path(self) -> None:
        self.paths_to_export.append(f"{self.install_path}/approximate-integration/bin")
