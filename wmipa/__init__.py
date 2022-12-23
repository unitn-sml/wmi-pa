# check whether MathSAT is installed or not
try:
    import mathsat
except ImportError:
    IMPORT_ERR_MSG = """Couldn't import mathsat.
MathSAT needs to be manually installed via:
    pysmt-install --msat"""

from .log import logger
from .wmi import WMI
