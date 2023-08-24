import os
import sys

from wmipa_cli.installers.installer import Installer
from wmipa_cli.log import logger


class SymbolicInstaller(Installer):
    """Install symbolic integrator dependencies.
    The symbolic integrator depends on PyXadd, that can be installed via pywmi as:
    pip install git+https://github.com/weighted-model-integration/pywmi.git#egg=pywmi
    pywmi-install --pyxadd
    """

    def __init__(self, install_path):
        super().__init__(install_path)
        self.repo_url = "git+https://github.com/weighted-model-integration/pywmi.git#egg=pywmi"

    def get_name(self):
        return "Symbolic Integrator (PyXadd)"

    def check_environment(self, yes):
        return True

    def download(self):
        pass

    def unpack(self):
        pass

    def build(self):
        logger.info(f"Installing pywmi from pip...")
        os.system(f"{sys.executable} -m pip install {self.repo_url}")

    def add_to_path(self):
        pass
