__version__ = "0.999"
__author__ = "Paolo Morettin"

from subprocess import call

from wmipa.integration.command_line_integrator import CommandLineIntegrator


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
