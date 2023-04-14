import os
from logging import warning

from wmipa_cli.installers.installer import Installer
from wmipa_cli.utils import check_os_version


class VolestiInstaller(Installer):
    dependencies = ["cmake", "g++", "make"]

    def __init__(self, install_path):
        super().__init__(install_path)
        self.git_repo = "https://github.com/masinag/approximate-integration"

    def get_name(self):
        return "Volesti Integrator"

    def check_environment(self):
        print(f"Checking environment for {self.get_name()}...")
        if not check_os_version("Linux"):
            warning(f"""Automatic installation of {self.get_name()} is supported only for Linux.
        Please install it manually from {self.git_repo}""")
            return False
        if not self.ask_dependencies_proceed():
            return False
        return True

    def ask_dependencies_proceed(self):
        print("Make sure you have the following dependencies installed:")
        print(" ".join(self.dependencies))
        print("Do you want to proceed? [y/n] ", end="")
        return input().strip().lower() == "y"

    def download(self):
        if os.path.exists("approximate-integration"):
            print(f"Skipping download of {self.get_name()}, directory approximate-integration already exists.")
            return
        print(f"Downloading {self.get_name()}...")
        os.system(f"git clone {self.git_repo}")

    def unpack(self):
        pass

    def build(self):
        os.chdir("approximate-integration")
        os.system("make")

    def add_to_path(self):
        self.paths_to_export.append(f"{self.install_path}/approximate-integration/bin")
