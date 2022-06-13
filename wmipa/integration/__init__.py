from shutil import which

IMPORT_ERR_MSG = None

# check whether LattE integrale is installed or not
if IMPORT_ERR_MSG is None and which("integrate") is None:
    IMPORT_ERR_MSG = """LattE integrale is not installed or its binaries are not included in PATH"""

# check whether VolEsti is installed or not
if IMPORT_ERR_MSG is None and which("volesti_integrate_polynomial") is None:
    IMPORT_ERR_MSG = """VolEsti is not installed or its binaries are not included in PATH"""

if IMPORT_ERR_MSG:
    raise ImportError(IMPORT_ERR_MSG)
else:
    from .integrator import Integrator
    from .cache_integrator import CacheIntegrator
    from .command_line_integrator import CommandLineIntegrator
    from .latte_integrator import LatteIntegrator
    from .volesti_integrator import VolestiIntegrator
