import os
import sys

from wmipa_cli.installers.installer import Installer
from wmipa_cli.log import logger
from wmipa_cli.utils import safe_cmd


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

    def build(self, force):
        logger.info(f"Installing pywmi from pip...")
        force_str = "--force-reinstall" if force else ""
        safe_cmd(f"{sys.executable} -m pip install {self.repo_url} {force_str}")

    def add_to_path(self):
        pass
