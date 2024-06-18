from shutil import which


def _is_latte_installed():
    return which("integrate") is not None


def _is_volesti_installed():
    return which("volesti_integrate") is not None


IMPORT_ERR_MSG = "No integration backend installed. Run `wmipa-install --help` for more information."

if not any((_is_latte_installed(), _is_volesti_installed())):
    raise ImportError(IMPORT_ERR_MSG)
else:
    from .latte_integrator import LatteIntegrator
    from .volesti_integrator import VolestiIntegrator
