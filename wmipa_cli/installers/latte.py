import os

from wmipa_cli.installers.installer import Installer
from wmipa_cli.log import logger
from wmipa_cli.utils import check_os_version, safe_cmd, remove_suffix


class LatteInstaller(Installer):
    dependencies = ['g++', 'libboost-dev', 'libcdd-dev', 'libcdd-tools', 'libgmp-dev', 'libmpfr-dev', 'libntl-dev',
                    'make', 'wget']

    def __init__(self, install_path, version=(1, 7, 6)):
        super().__init__(install_path)
        self.download_url = self.get_download_url(version)
        self.filename = self.get_filename(version)

    def get_name(self):
        return "LattE Integrale"

    def get_dir(self):
        return "latte"

    @staticmethod
    def get_filename(version):
        return "latte-int-{}.{}.{}.tar.gz".format(version[0], version[1], version[2])

    @staticmethod
    def get_download_url(version):
        return "https://github.com/latte-int/latte/releases/download/" \
               "version_{a}_{b}_{c}/latte-int-{a}.{b}.{c}.tar.gz".format(
            a=version[0], b=version[1], c=version[2])

    def check_environment(self, yes):
        logger.info(f"Checking environment for {self.get_name()}...")
        if not check_os_version("Linux"):
            logger.error(f"""Automatic installation of {self.get_name()} is supported only for Linux.
        Please install it manually from {self.download_url}""")
            return False
        if not self.ask_dependencies_proceed(yes):
            return False
        return True

    def ask_dependencies_proceed(self, yes):
        logger.info("Make sure you have the following dependencies installed:")
        logger.info(" ".join(self.dependencies))
        logger.info("Do you want to proceed? [y/n] ")
        return yes or input().strip().lower() == "y"

    def download(self):
        filename = os.path.basename(self.filename)
        if os.path.exists(self.filename):
            logger.info(f"Skipping download of {self.get_name()}, file {self.filename} already exists.")
            return
        logger.info(f"Downloading {self.get_name()} from {self.download_url} to {os.getcwd()}...")
        safe_cmd("wget %s" % self.download_url)

    def unpack(self):
        dirname = self._dirname()
        if os.path.exists(dirname):
            logger.info(f"Skipping unpacking of {self.get_name()}, directory {dirname} already exists.")
            return
        logger.info(f"Unpacking {self.get_name()} to {os.getcwd()}...")
        safe_cmd(f"tar -xzf {self.filename}")
        safe_cmd(f"rm {self.filename}")

    def build(self, force):
        logger.info("Configuring and building LattE Integrale...")
        dirname = self._dirname()
        os.chdir(dirname)
        bin_path = os.path.abspath(os.path.join(self.install_path, self.get_dir()))
        if force and os.path.exists(bin_path):
            safe_cmd(f"rm -rf {bin_path}")
        safe_cmd(f'./configure GXX="g++ -std=c++11" CXX="g++ -std=c++11" '
                 f'--prefix={bin_path} && make && make install')

    def _dirname(self):
        return remove_suffix(os.path.basename(self.filename), ".tar.gz")

    def add_to_path(self):
        self.paths_to_export.append(f'PATH={self.install_path}/{self.get_dir()}/bin')
