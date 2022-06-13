__version__ = "0.999"
__author__ = "Gabriele Masina"

from subprocess import call

from wmipa.integration.command_line_integrator import CommandLineIntegrator
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
        walk_type (str): The type of random walk to use.
        N (int): Number of samples.
        walk_length (int): Length of random walk.

    """

    ALG_SEQUENCE_OF_BALLS = "SOB"
    ALG_COOLING_BALLS = "CB"
    ALG_COOLING_GAUSSIANS = "CG"
    DEF_ALGORITHM = ALG_COOLING_BALLS

    ALGORITHMS = [
        ALG_SEQUENCE_OF_BALLS,
        ALG_COOLING_BALLS,
        ALG_COOLING_GAUSSIANS,
    ]

    RW_BALL_WALK = "Ba"
    RW_RDHR = "RDHR"
    RW_CDHR = "CDHR"
    RW_BILLIARD_WALK = "Bi"
    RW_ACCELERATED_BILLIARD_WALK = "ABi"
    DEF_RANDOM_WALK = RW_CDHR

    RANDOM_WALKS = [
        RW_BALL_WALK,
        RW_RDHR,
        RW_CDHR,
        RW_BILLIARD_WALK,
        RW_ACCELERATED_BILLIARD_WALK,
    ]

    DEF_ERROR = 1e-1
    DEF_N = 1000
    DEF_WALK_LENGTH = 0

    def __init__(self, **options):
        """Default constructor.

        Args:
            **options:
                - algorithm: Defines the algorithm to use when integrating.
                - n_threads: Defines the number of threads to use.
                - stub_integrate: If True the integrals will not be computed.
                - error: The relative error tolerated (in (0.0, 1.0)).
                - walk_type: The type of random walk to use.
                - N: Number of samples.
                - walk_length: Length of random walk.

        """
        CommandLineIntegrator.__init__(self, **options)
        self.error = options.get("error") or self.DEF_ERROR
        if not (0.0 < self.error < 1.0):
            err = "{}, error must be in (0.0, 1.0)".format(self.error)
            raise WMIRuntimeException(WMIRuntimeException.OTHER_ERROR, err)
        self.walk_type = options.get("walk_type") or self.DEF_RANDOM_WALK
        if self.walk_type not in self.RANDOM_WALKS:
            err = "{}, choose one from: {}".format(
                self.walk_type, ", ".join(self.RANDOM_WALKS)
            )
            raise WMIRuntimeException(WMIRuntimeException.INVALID_MODE, err)
        self.N = options.get("N") or self.DEF_N
        if self.N <= 0:
            err = "{}, N must be a positive number".format(self.N)
            raise WMIRuntimeException(WMIRuntimeException.OTHER_ERROR, err)
        self.walk_length = options.get("walk_length") or self.DEF_WALK_LENGTH
        if self.walk_length < 0:
            err = "{}, walk_length must be a non-negative number".format(
                self.walk_length
            )
            raise WMIRuntimeException(WMIRuntimeException.OTHER_ERROR, err)

    def _call_integrator(self, polynomial_file, polytope_file, output_file):
        """Calls VolEsti executable to calculate the integrand of the problem
            represented by the given files.

        Args:
            polynomial_file (str): The path where to find the file with the
                representation of the polynomial.
            polytope_file (str): The path where to find the file with representation
                of the polytope.
            output_file (str): The file where to write the result of the computation.

        """
        cmd = [
            "volesti_integrate_polynomial",
            polytope_file,
            polynomial_file,
            str(self.error),
            "--volume",
            self.algorithm,
            "--walk",
            self.walk_type,
            "--N",
            str(self.N),
            "--wlength",
            str(self.walk_length),
        ]

        with open(output_file, "w") as f:
            if self.stub_integrate:
                f.write("")
            else:
                return_value = call(cmd, stdout=f, stderr=f)
