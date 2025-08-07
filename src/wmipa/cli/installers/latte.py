import os
import platform
import shutil
import tarfile
import urllib.request
from pathlib import Path

from wmipa.cli.installers.installer import Installer
from wmipa.cli.log import logger
from wmipa.cli.utils import safe_cmd


class LatteInstaller(Installer):
    linux_dependencies = [
        "libboost-dev",
        "libcdd-dev",
        "libcdd-tools",
        "libgmp-dev",
        "libmpfr-dev",
        "libntl-dev",
        "make",
    ]
    macos_dependencies = ["boost", "gmp", "mpfr", "ntl"]

    def __init__(
        self,
        install_path: str,
        include_paths: list[str],
        lib_paths: list[str],
        cxx: str,
        version: tuple[int, int, int] = (1, 7, 6),
    ):
        super().__init__(install_path, include_paths, lib_paths)
        self.version = version
        self.cxx = cxx
        self.download_url = self.get_download_url(version)
        self.filename = self.get_filename(version)
        self.system = platform.system().lower()

    @staticmethod
    def get_name() -> str:
        return "LattE Integrale"

    @staticmethod
    def get_dir() -> str:
        return "latte"

    @staticmethod
    def get_filename(version: tuple[int, int, int]) -> str:
        return "latte-int-{}.{}.{}.tar.gz".format(version[0], version[1], version[2])

    @staticmethod
    def get_download_url(version: tuple[int, int, int]) -> str:
        return (
            "https://github.com/latte-int/latte/releases/download/"
            "version_{a}_{b}_{c}/latte-int-{a}.{b}.{c}.tar.gz".format(
                a=version[0], b=version[1], c=version[2]
            )
        )

    def get_dependencies(self) -> list[str]:
        if self.system == "linux":
            return self.linux_dependencies
        elif self.system == "darwin":  # macOS
            return self.macos_dependencies
        else:
            return []

    def check_environment(self, yes: bool) -> bool:
        logger.info(f"Checking environment for {self.get_name()}...")

        if self.system not in ["linux", "darwin"]:
            logger.error(
                f"Automatic installation of {self.get_name()} is not supported on {platform.system()}."
            )
            logger.error(f"Please install it manually from {self.download_url}")
            return False

        if not self.ask_dependencies_proceed(yes):
            return False

        return True

    def ask_dependencies_proceed(self, yes: bool) -> bool:
        dependencies = self.get_dependencies()
        if not dependencies:
            return True

        logger.info("Make sure you have the following dependencies installed:")
        logger.info(" ".join(dependencies))

        if yes:
            return True

        logger.info("\nDo you want to proceed? [y/n] ")
        return input().strip().lower() == "y"

    def download(self) -> None:
        filename = Path(self.filename).name
        if Path(filename).exists():
            logger.info(
                f"Skipping download of {self.get_name()}, file {filename} already exists."
            )
            return

        logger.info(f"Downloading {self.get_name()} from {self.download_url}...")

        urllib.request.urlretrieve(self.download_url, filename)

    def unpack(self) -> None:
        dirname = self._dirname()
        if Path(dirname).exists():
            logger.info(
                f"Skipping unpacking of {self.get_name()}, directory {dirname} already exists."
            )
            return

        logger.info(f"Unpacking {self.get_name()}...")

        with tarfile.open(self.filename, "r:gz") as tar:
            tar.extractall()
        logger.info(f"Extracted to {dirname}")

        Path(self.filename).unlink()  # Clean-up archive

    def build(self, force: bool = False) -> None:
        logger.info("Configuring and building LattE Integrale...")
        dirname = self._dirname()
        os.chdir(dirname)

        bin_path = Path(self.install_path) / self.get_dir()
        bin_path = bin_path.resolve()  # Get the absolute path

        if bin_path.exists():
            if force:
                logger.info(f"Removing existing installation at {bin_path}")
                shutil.rmtree(bin_path)
            else:
                logger.info(
                    f"Skipping build, {self.get_name()} already installed at {bin_path}"
                )
                return

        # Ensure install directory exists
        bin_path.mkdir(parents=True, exist_ok=True)

        # Platform-specific build configuration
        if self.system in ["linux", "darwin"]:
            self._build_unix(str(bin_path))
        else:
            raise RuntimeError(
                f"Unsupported system: {self.system}. LattE Integrale can only be built on Linux or macOS."
            )

    def _build_unix(self, bin_path: str) -> None:
        """Build on Unix systems (Linux, macOS)"""
        env = os.environ.copy()
        env["CXX"] = self.cxx
        env["CXXFLAGS"] = env.get("CXXFLAGS", "") + " -std=c++11"
        env["CPPFLAGS"] = env.get("CPPFLAGS", "") + " ".join(
            f"-I{p}" for p in self.include_paths
        )
        env["LDFLAGS"] = env.get("LDFLAGS", "") + " ".join(
            f"-L{p}" for p in self.lib_paths
        )

        configure_cmd = [
            "./configure",
            f"--prefix={bin_path}",
            "--with-gmp=yes",
            "--with-ntl=yes",
            "--with-cddlib=yes",
            "--disable-dependency-tracking",
        ]

        safe_cmd(configure_cmd, env=env)
        safe_cmd(["make"], env=env)
        safe_cmd(["make", "install"], env=env)

    def _dirname(self) -> str:
        return Path(self.filename).name.removesuffix(".tar.gz")

    def add_to_path(self) -> None:
        bin_dir = Path(self.install_path) / self.get_dir() / "bin"
        self.paths_to_export.append(str(bin_dir))
