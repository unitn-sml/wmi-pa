__version__ = '0.999'
__author__ = 'Gabriele Masina'
__version__ = '0.999'
__author__ = 'Paolo Morettin'

from subprocess import call

from wmipa.integrator import CacheIntegrator
from wmipa.wmiexception import WMIRuntimeException


class VolestiIntegrator(CommandLineIntegrator):
    """This class handles the approximated integration of polynomial functions 
    over (convex) polytopes.

    It inherits from the abstract class CacheIntegrator.

    VolEsti is required.

    Attributes:
        algorithm (str): The algorithm to use when computing the integrals.
        n_threads (int): The number of threads to use.
        error (int): The relative error tolerated (in (0.0, 1.0))

    """

    ALG_SEQUENCE_OF_BALLS = "SOB"
    ALG_COOLING_BALLS = "CB"
    ALG_COOLING_GAUSSIANS = "CG"
    DEF_ALGORITHM = ALG_COOLING_GAUSSIANS

    ALGORITHMS = [
        ALG_SEQUENCE_OF_BALLS,
        ALG_COOLING_BALLS,
        ALG_COOLING_GAUSSIANS]

    DEF_ERROR = 1e-4

    def __init__(self, **options):
        """Default constructor.

        Args:
            **options:
                - algorithm: Defines the algorithm to use when integrating.
                - n_threads: Defines the number of threads to use.
                - error: The relative error tolerated (in (0.0, 1.0))
                - stub_integrate: If True the integrals will not be computed

        """
        CacheIntegrator.__init__(self, **options)
        self.error = options.get('error') or self.DEF_ERROR
        if not (0.0 < self.error < 1.0):
            err = '{}, error must be in (0.0, 1.0)'.format(self.error)
            raise WMIRuntimeException(WMIRuntimeException.OTHER_ERROR, err)

    def _call_integrator(self, polynomial_file, polytope_file, output_file):
        """Calls VolEsti executable to calculate the integrand of the problem
            represented by the given files.

        Args:
            polynomial_file (str): The path where to find the file with the representation of the polynomial.
            polytope_file (str): The path where to find the file with representation of the polytope.
            output_file (str): The file where to write the result of the computation.

        """
        cmd = ["volesti_integrate_polynomial",
               polytope_file,
               polynomial_file,
               str(self.error),
               self.algorithm
               ]

        with open(output_file, 'w') as f:
            if self.stub_integrate:
                f.write("")
            else:
                return_value = call(cmd, stdout=f, stderr=f)
