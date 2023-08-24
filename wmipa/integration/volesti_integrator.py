__version__ = "0.999"
__author__ = "Gabriele Masina"

from subprocess import call

from wmipa.integration import _is_volesti_installed
from wmipa.integration.command_line_integrator import CommandLineIntegrator
from wmipa.integration.expression import Expression
from wmipa.integration.polytope import Polytope
from wmipa.wmiexception import WMIRuntimeException, WMIIntegrationException

_VOLESTI_INSTALLED = _is_volesti_installed()


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
    DEF_SEED = None  # unset
    DEF_WALK_LENGTH = None  # let the tool choose
    DEF_N = 1000

    def __init__(self,
                 algorithm=DEF_ALGORITHM,
                 error=DEF_ERROR,
                 walk_type=DEF_RANDOM_WALK,
                 walk_length=DEF_WALK_LENGTH,
                 seed=DEF_SEED,
                 N=DEF_N,
                 **options
                 ):
        """Default constructor.

        Args:
            algorithm: Defines the algorithm to use when integrating.
            error: The relative error tolerated (in (0.0, 1.0)).
            walk_type: The type of random walk to use.
            N: Number of samples.
            walk_length: Length of random walk.
            options: @see CommandLineIntegrator.__init__

        """
        CommandLineIntegrator.__init__(self, **options)

        self.algorithm = algorithm
        if self.algorithm not in self.ALGORITHMS:
            err = "{}, choose one from: {}".format(
                self.algorithm, ", ".join(self.ALGORITHMS)
            )
            raise WMIRuntimeException(WMIRuntimeException.INVALID_MODE, err)

        self.error = error
        if not (0.0 < self.error < 1.0):
            err = "{}, error must be in (0.0, 1.0)".format(self.error)
            raise WMIRuntimeException(WMIRuntimeException.OTHER_ERROR, err)

        self.walk_type = walk_type
        if self.walk_type not in self.RANDOM_WALKS:
            err = "{}, choose one from: {}".format(
                self.walk_type, ", ".join(self.RANDOM_WALKS)
            )
            raise WMIRuntimeException(WMIRuntimeException.INVALID_MODE, err)

        self.walk_length = walk_length
        if self.walk_length is not None and self.walk_length < 0:
            err = "{}, walk_length must be a non-negative number".format(
                self.walk_length
            )
            raise WMIRuntimeException(WMIRuntimeException.OTHER_ERROR, err)

        self.N = N
        if self.N <= 0:
            err = "{}, N must be a positive number".format(self.N)
            raise WMIRuntimeException(WMIRuntimeException.OTHER_ERROR, err)

        self.seed = seed
        if self.seed is not None and self.seed < 0:
            err = "{}, seed must be a non-negative number".format(self.seed)
            raise WMIRuntimeException(WMIRuntimeException.OTHER_ERROR, err)

    def _write_integrand_file(self, integrand, variables, path):
        """Writes the integrand to the given file.

        Args:
            integrand (Expression): The integrand.
            variables (list): The list of variables.
            path (str): The path where to write the integrand.

        """
        with open(path, "w") as f:
            f.write("{} \n {} \n".format(" ".join(variables), str(integrand)))

    @classmethod
    def _make_problem(cls, weight, bounds, aliases):
        """Makes the problem to be solved by VolEsti.
        Args:
            weight (FNode): The weight function.
            bounds (list): The polytope.
            aliases (dict): The aliases of the variables.
        Returns:
            integrand (Expression): The integrand.
            polytope (Polytope): The polytope.
        """
        integrand = Expression(weight, aliases)
        polytope = Polytope(bounds, aliases)
        return integrand, polytope

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
        if not _VOLESTI_INSTALLED:
            raise WMIIntegrationException(WMIIntegrationException.INTEGRATOR_NOT_INSTALLED, "VolEsti")

        cmd = [
            "volesti_integrate",
            polytope_file,
            polynomial_file,
            str(self.error),
            "--volume",
            self.algorithm,
            "--walk",
            self.walk_type,
            "--N",
            str(self.N),
        ]
        if self.walk_length is not None:
            cmd += ["--wlength", str(self.walk_length)]
        if self.seed is not None:
            cmd += ["--seed", str(self.seed)]

        with open(output_file, "w") as f:
            if self.stub_integrate:
                f.write("")
            else:
                return_value = call(cmd, stdout=f)
                if return_value != 0:
                    raise WMIIntegrationException(WMIIntegrationException.OTHER_ERROR, "Error while calling VolEsti")
