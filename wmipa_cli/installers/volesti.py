import os
from wmipa_cli.log import logger

from wmipa_cli.installers.installer import Installer
from wmipa_cli.utils import check_os_version


class VolestiInstaller(Installer):
    dependencies = ["cmake", "g++", "make"]

    def __init__(self, install_path):
        super().__init__(install_path)
        self.git_repo = "https://github.com/masinag/approximate-integration"

    def get_name(self):
        return "Volesti Integrator"

    def check_environment(self, yes):
        logger.info(f"Checking environment for {self.get_name()}...")
        if not check_os_version("Linux"):
            logger.warning(f"""Automatic installation of {self.get_name()} is supported only for Linux.
        Please install it manually from {self.git_repo}""")
            return False
        if not self.ask_dependencies_proceed(yes):
            return False
        return True

    def ask_dependencies_proceed(self, yes):
        logger.info("Make sure you have the following dependencies installed:")
        logger.info(" ".join(self.dependencies))
        logger.info("Do you want to proceed? [y/n] ", end="")
        return yes or input().strip().lower() == "y"

    def download(self):
        if os.path.exists("approximate-integration"):
            logger.info(f"Skipping download of {self.get_name()}, directory approximate-integration already exists.")
            return
        logger.info(f"Downloading {self.get_name()}...")
        os.system(f"git clone {self.git_repo}")

    def unpack(self):
        pass

    def build(self):
        os.chdir("approximate-integration")
        os.system("make")

    def add_to_path(self):
        self.paths_to_export.append(f"{self.install_path}/approximate-integration/bin")
