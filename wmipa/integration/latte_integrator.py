__version__ = "0.999"
__author__ = "Paolo Morettin"

from subprocess import call

from wmipa.integration import _is_latte_installed
from wmipa.integration.command_line_integrator import CommandLineIntegrator
from wmipa.integration.polytope import Polynomial, Polytope
from wmipa.wmiexception import WMIRuntimeException, WMIIntegrationException

_LATTE_INSTALLED = _is_latte_installed()


class LatteIntegrator(CommandLineIntegrator):
    """This class handles the integration of polynomial functions over (convex) polytopes.

    It inherits from the abstract class CacheIntegrator.

    LattE Integrale is required.

    Attributes:
        algorithm (str): The algorithm to use when computing the integrals.
        n_threads (int): The number of threads to use.

    """

    ALG_TRIANGULATE = "--triangulate"
    ALG_CONE_DECOMPOSE = "--cone-decompose"
    DEF_ALGORITHM = ALG_CONE_DECOMPOSE

    ALGORITHMS = [ALG_TRIANGULATE, ALG_CONE_DECOMPOSE]

    def __init__(self, algorithm=DEF_ALGORITHM, **options):
        """Default constructor.

        It calls the init method of the parent.

        Args:
            algorithm (str): The algorithm to use when computing the integrals.
            options: @see CommandLineIntegrator.__init__

        """
        super().__init__(**options)
        self.algorithm = algorithm

        # check that algorithm exists
        if self.algorithm not in self.ALGORITHMS:
            err = "{}, choose one from: {}".format(
                self.algorithm, ", ".join(self.ALGORITHMS)
            )
            raise WMIRuntimeException(WMIRuntimeException.INVALID_MODE, err)

    @classmethod
    def _make_problem(cls, weight, bounds, aliases):
        """Makes the problem to be solved by LattE.
        Args:
            weight (FNode): The weight function.
            bounds (list): The polytope.
            aliases (dict): The aliases of the variables.
        Returns:
            integrand (Polynomial): The integrand.
            polytope (Polytope): The polytope.
        """
        integrand = Polynomial(weight, aliases)
        polytope = Polytope(bounds, aliases)

        return integrand, polytope

    def _write_integrand_file(self, integrand, variables, path):
        """Writes the integrand to the given file.

        Args:
            integrand (Polynomial): The integrand.
            variables (list): The list of variables.
            path (str): The path where to write the file.

        """
        # Create the string representation of the integrand (LattE format)
        monomials_repr = []
        for monomial in integrand.monomials:
            monomial_repr = "[" + str(monomial.coefficient) + ",["
            exponents = []
            for var in variables:
                if var in monomial.exponents:
                    exponents.append(str(monomial.exponents[var]))
                else:
                    exponents.append("0")
            monomial_repr += ",".join(exponents) + "]]"
            monomials_repr.append(monomial_repr)
        latte_repr = "[" + ",".join(monomials_repr) + "]"

        # Write the string on the file
        with open(path, "w") as f:
            f.write(latte_repr)

    def _call_integrator(self, polynomial_file, polytope_file, output_file):
        """Calls LattE executable to calculate the integrand of the problem
            represented by the given files.

        Args:
            polynomial_file (str): The path where to find the file with the
                representation of the polynomial.
            polytope_file (str): The path where to find the file with representation
                of the polytope.
            output_file (str): The file where to write the result of the computation.

        """
        if not _LATTE_INSTALLED:
            raise WMIIntegrationException(WMIIntegrationException.INTEGRATOR_NOT_INSTALLED, "LattE")

        cmd = [
            "integrate",
            "--valuation=integrate",
            self.algorithm,
            "--monomials=" + polynomial_file,
            polytope_file,
        ]

        with open(output_file, "w") as f:
            if self.stub_integrate:
                f.write("")
            else:
                return_value = call(cmd, stdout=f, stderr=f)
                if return_value != 0:
                    # print(open(output_file).read())
                    """
                    if return_value != 0:
                        msg = "LattE returned with status {}"
                        # LattE returns an exit status != 0 if the polytope is empty.
                        # In the general case this may happen, raising an exception
                        # is not a good idea.
                    """
            return_value = call(cmd, stdout=f, stderr=f)
            if return_value != 0:
                # print(open(output_file).read())
                """
                if return_value != 0:
                    msg = "LattE returned with status {}"
                    # LattE returns an exit status != 0 if the polytope is empty.
                    # In the general case this may happen, raising an exception
                    # is not a good idea.
                """
