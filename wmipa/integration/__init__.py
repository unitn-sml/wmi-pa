from shutil import which

IMPORT_ERR_MSG = "No integration backend installed."
latte_installed = True
volesti_installed = True

# check whether LattE integrale is installed or not
if which("integrate") is None:
    latte_installed = False

# check whether VolEsti is installed or not
if which("volesti_integrate") is None:
    volesti_installed = False

if not any([latte_installed, volesti_installed]):
    raise ImportError(IMPORT_ERR_MSG)
else:
    from .integrator import Integrator
    from .cache_integrator import CacheIntegrator
    from .command_line_integrator import CommandLineIntegrator
    from .latte_integrator import LatteIntegrator
    from .volesti_integrator import VolestiIntegrator
