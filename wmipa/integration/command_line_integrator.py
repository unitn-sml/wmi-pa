from abc import abstractmethod
from os import chdir, getcwd
from tempfile import TemporaryDirectory

from wmipa.integration.cache_integrator import CacheIntegrator
from wmipa.wmiexception import WMIRuntimeException

class WMICommandLineIntegratorException(WMIRuntimeException):
    """
    Exception raised when the command line integrator fails.
    """

    MEMORY_LIMIT = 0
    UNBOUNDED_POLYHEDRON = 1

    messages = {
        MEMORY_LIMIT: "Memory limit exceeded (maybe)",
        UNBOUNDED_POLYHEDRON: "Unbounded polyhedron",
    }

    def __init__(self, code, value=None):
        """
        Default constructor.

        It calls the init method of the parent.

        Args:
            code (int): The code of the exception.
            value: Additional info about the value that raised the exception (default: None).

        """
        super().__init__(code, value)

class CommandLineIntegrator(CacheIntegrator):
    DEF_ALGORITHM = None
    ALGORITHMS = []
    # Template name for the temporary folder
    FOLDER_TEMPLATE = "tmp_{}"

    # Temporary files
    POLYTOPE_TEMPLATE = "polytope.hrep"
    INTEGRAND_TEMPLATE = "integrand.txt"
    OUTPUT_TEMPLATE = "output.txt"

    def __init__(self, **options):
        super().__init__(**options)

    def _integrate_problem(self, integrand, polytope):
        """Generates the input files and calls integrator executable
            to calculate the integral. Then, reads back the result and returns it
            as a float.

        Args:
            integrand (Integrand): The integrand of the integration.
            polytope (Polytope): The polytope of the integration.

        Returns:
            real: The integration result.

        """
        # Create a temporary folder containing the input and output files
        # possibly removing an older one
        with TemporaryDirectory(dir=".") as folder:
            integrand_file = self.INTEGRAND_TEMPLATE
            polytope_file = self.POLYTOPE_TEMPLATE
            output_file = self.OUTPUT_TEMPLATE

            # Change the CWD
            original_cwd = getcwd()
            chdir(folder)

            # Variable ordering is relevant in LattE files
            variables = sorted(integrand.variables.union(polytope.variables))

            # Write integrand and polytope to file
            self._write_integrand_file(integrand, variables, integrand_file)
            self._write_polytope_file(polytope, variables, polytope_file)
            # key = tuple([polytope_key, cond_assignments])

            # if cache:
            #     value = self.hashTable.get(key)
            #     if value is not None:
            #         chdir(original_cwd)
            #         return value, 1

            # Integrate and dump the result on file
            self._call_integrator(integrand_file, polytope_file, output_file)

            # Read back the result and return to the original CWD
            result = self._read_output_file(output_file)
            chdir(original_cwd)

            return result

    def _read_output_file(self, path):
        """Reads the output file generated by the computation of the integrator.

        Args:
            path (str): The path of the file to read.

        Returns:
            real: The result of the computation written in the file.

        """
        res = None

        with open(path, "r") as f:
            lines = f.readlines()
            for line in lines:
                # Result in the "Answer" line may be written in fraction form
                if "Decimal" in line:
                    # print("Res: {}".format(line))
                    return float(line.partition(": ")[-1].strip())

            # error (possibly interrupted due to memory limit)
            if "Cannot compute valuation for unbounded polyhedron." in ' '.join(lines):
                error = WMICommandLineIntegratorException.UNBOUNDED_POLYHEDRON
            else:
                error = WMICommandLineIntegratorException.MEMORY_LIMIT
            raise WMICommandLineIntegratorException(error)

        return res

    @abstractmethod
    def _write_integrand_file(self, integrand, variables, path):
        """Writes the integrand into a file from where the integrator will read.

        Args:
            integrand (Integrand): The integrand of the integration.
            variables (list): The sorted list of all the variables involved in the
                integration.
            path (str): The path of the file to write.
        """
        pass

    def _write_polytope_file(self, polytope, variables, path):
        """Writes the polytope into a file from where the integrator will read.

        Args:
            polytope (Polytope): The polytope of the integration.
            variables (list): The sorted list of all the variables involved in the
                integration.
            path (str): The path of the file to write.
        """
        # Create the string representation of the polytope (LattE format)
        n_ineq = str(len(polytope.bounds))
        n_vars = str(len(variables) + 1)
        latte_repr = "{} {}\n".format(n_ineq, n_vars)
        for _, bound in enumerate(polytope.bounds):
            latte_repr += str(bound.constant) + " "
            for var in variables:
                if var in bound.coefficients:
                    latte_repr += str(-bound.coefficients[var]) + " "
                else:
                    latte_repr += "0 "
            latte_repr += "\n"

        # Write the string on the file
        with open(path, "w") as f:
            f.write(latte_repr)

    @abstractmethod
    def _call_integrator(self, polynomial_file, polytope_file, output_file):
        pass
