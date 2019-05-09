
from shutil import which

IMPORT_ERR_MSG = None

# check whether MathSAT is installed or not
try:
    import mathsat
except ImportError:
    IMPORT_ERR_MSG = """Couldn't import mathsat.
MathSAT needs to be manually installed via:
    pysmt-install --msat"""

# check whether LattE integrale is installed or not
if IMPORT_ERR_MSG is None and which('integrate') is None:
    IMPORT_ERR_MSG = """LattE integrale is not installed or its binaries are not included in PATH"""

if IMPORT_ERR_MSG:
    raise ImportError(IMPORT_ERR_MSG)
else:
    from .log import logger
    from .wmi import WMI

