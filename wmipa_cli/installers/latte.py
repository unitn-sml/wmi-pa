import os
from logging import warning

from wmipa_cli.installers.installer import Installer
from wmipa_cli.utils import check_os_version


class LatteInstaller(Installer):
    dependencies = ['g++', 'libboost-dev', 'libcdd-dev', 'libcdd-tools', 'libgmp-dev', 'libmpfr-dev', 'libntl-dev',
                    'make', 'wget']

    def __init__(self, install_path, version=(1, 7, 6)):
        super().__init__(install_path)
        self.download_url = self.get_download_url(version)
        self.filename = self.get_filename(version)

    def get_name(self):
        return "LattE Integrale"

    @staticmethod
    def get_filename(version):
        return "latte-int-{}.{}.{}.tar.gz".format(version[0], version[1], version[2])

    @staticmethod
    def get_download_url(version):
        return "https://github.com/latte-int/latte/releases/download/" \
               "version_{a}_{b}_{c}/latte-int-{a}.{b}.{c}.tar.gz".format(
            a=version[0], b=version[1], c=version[2])

    def check_environment(self):
        print(f"Checking environment for {self.get_name()}...")
        if not check_os_version("Linux"):
            warning(f"""Automatic installation of {self.get_name()} is supported only for Linux.
        Please install it manually from {self.download_url}""")
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
        if os.path.exists(self.filename) or os.path.exists(self.filename.rstrip("tar.gz")):
            print(f"Skipping download of {self.get_name()}, file {self.filename} already exists.")
            return
        print(f"Downloading {self.get_name()} from {self.download_url} to {os.getcwd()}...")
        os.system("wget %s" % self.download_url)

    def unpack(self):
        if os.path.exists(self.filename.rstrip("tar.gz")):
            print(
                f"Skipping unpacking of {self.get_name()}, directory {self.filename.rstrip('tar.gz')} already exists.")
            return
        print(f"Unpacking {self.get_name()}  to {os.getcwd()}...")
        os.system(f"tar -xzf {self.filename}")
        os.system(f"rm {self.filename}")

    def build(self):
        print("Configuring and building LattE Integrale...")
        dirname = self.filename.rstrip(".tar.gz")
        os.chdir(dirname)
        os.system(f'./configure GXX="g++ -std=c++11" CXX="g++ -std=c++11" '
                  f'--prefix={self.install_path}/latte && make && make install')

    def add_to_path(self):
        self.paths_to_export.append(f'PATH={self.install_path}/latte/bin')
