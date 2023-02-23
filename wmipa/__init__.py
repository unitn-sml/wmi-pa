# check whether MathSAT is installed or not
from logging import warning


def msat_version_supports_skeleton():
    return mathsat.msat_get_version().startswith("MathSAT5 version a479a24616e7")


try:
    import mathsat
except ImportError:
    IMPORT_ERR_MSG = """Couldn't import mathsat.
MathSAT needs to be manually installed via:
    pysmt-install --msat"""
    raise ImportError(IMPORT_ERR_MSG)

if not msat_version_supports_skeleton():
    IMPORT_WARN_MSG = """The installed version of MathSAT doesn't support the SA-PA-SK algorithm.
    run `wmipa-install --msat-custom` to install a custom version of MathSAT."""
    warning(IMPORT_WARN_MSG)

from .log import logger
from .wmi import WMI
