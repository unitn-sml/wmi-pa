"""This module implements the class that handles the integration of
polynomial functions over (convex) polytopes.

LattE Integrale is required.

"""

__version__ = '0.999'
__author__ = 'Paolo Morettin'

from subprocess import call
from os import makedirs, chdir, getcwd
from os.path import isdir
from shutil import rmtree
from fractions import Fraction
from tempfile import TemporaryDirectory

from wmipa.logger import Loggable
from wmipa.pysmt2latte import Polynomial, Polytope
from wmipa.wmiexception import WMIRuntimeException

class Integrator(Loggable):

    ALG_TRIANGULATE = "--triangulate"
    ALG_CONE_DECOMPOSE = "--cone-decompose"
    DEF_ALGORITHM = ALG_CONE_DECOMPOSE

    ALGORITHMS = [ALG_TRIANGULATE, ALG_CONE_DECOMPOSE]


    # template name for the temporary folder
    FOLDER_TEMPLATE = "latte_{}"
    # temporary files
    POLYTOPE_TEMPLATE = "polytope.hrep.latte"
    POLYNOMIAL_TEMPLATE = "polynomial.latte"
    OUTPUT_TEMPLATE = "output.txt"

    def __init__(self, algorithm=None):        
        self.init_sublogger(__name__)
        self.algorithm = algorithm or Integrator.DEF_ALGORITHM
        assert(self.algorithm in Integrator.ALGORITHMS)
            

    def integrate_raw(self, coefficients, rng, index=0):
        folder = TemporaryDirectory(dir=".")
        polynomial_file = Integrator.POLYNOMIAL_TEMPLATE
        polytope_file = Integrator.POLYTOPE_TEMPLATE
        output_file = Integrator.OUTPUT_TEMPLATE        
        # change the CWD and create the temporary files
        original_cwd = getcwd()
        chdir(folder.name)


        frac_coeffs = map(Fraction, coefficients)
        with open(polynomial_file, 'w') as f:
            f.write("[[{},[2]],[{},[1]],[{},[0]]]".format(*frac_coeffs))

        b1 = Fraction(rng[0]).denominator
        b2 = Fraction(rng[1]).denominator
        bound = [-Fraction(rng[0]).numerator, b1, Fraction(rng[1]).numerator, b2]

        with open(polytope_file, 'w') as f:
            f.write("2 2\n{} {}\n{} -{}".format(*bound))       
            
        # integrate and dump the result on file
        self._call_latte(polynomial_file, polytope_file, output_file)
        # read back the result and return to the original CWD
        result = self._read_output_file(output_file)
        
        chdir(original_cwd)

        return result
        

    def integrate(self, integrand, polytope, index=0):
        """Generates the input files and calls LattE's "integrate" executable
        to calculate the integral. Then, reads back the result and returns it
        as a float.

        Keyword arguments:
        integrand -- the polynomial
        polytope -- the bounds of the integral

        """
        assert(isinstance(integrand, Polynomial)
               and isinstance(polytope, Polytope)),\
               "Arguments should be of type Polynomial, Polytope."
        folder = TemporaryDirectory(dir=".")
        polynomial_file = Integrator.POLYNOMIAL_TEMPLATE
        polytope_file = Integrator.POLYTOPE_TEMPLATE
        output_file = Integrator.OUTPUT_TEMPLATE        
        # change the CWD and create the temporary files
        original_cwd = getcwd()
        chdir(folder.name)

        # variable ordering is relevant in LattE files 
        variables = list(integrand.variables.union(polytope.variables))
        variables.sort()

        self._write_polynomial_file(integrand, variables, polynomial_file)
        self._write_polytope_file(polytope, variables, polytope_file)
        # integrate and dump the result on file
        
        self._call_latte(polynomial_file, polytope_file, output_file)
        # read back the result and return to the original CWD
        result = self._read_output_file(output_file)

        chdir(original_cwd)
        return result

    def _read_output_file(self, path):
        res = None
        with open(path, 'r') as f:
            for line in f:
                # result in the "Answer" line may be written in fraction form
                if "Decimal" in line:
                    res = float(line.partition(": ")[-1].strip())
                    break

        return res
        
    def _write_polynomial_file(self, integrand, variables, path):
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

        with open(path, 'w') as f:
            f.write(latte_repr)

    def _write_polytope_file(self, polytope, variables, path):
        n_ineq = str(len(polytope.polytope))
        n_vars = str(len(variables) + 1)
        latte_repr = "{} {}\n".format(n_ineq, n_vars)
        for index, bound in enumerate(polytope.polytope):
            latte_repr += str(bound.constant) + " "
            for var in variables:
                if var in bound.coefficients:
                    latte_repr += str(-bound.coefficients[var]) + " "
                else:
                    latte_repr += "0 "
            latte_repr += "\n"

        with open(path, 'w') as f:
            f.write(latte_repr)

    def _call_latte(self, polynomial_file, polytope_file, output_file):
        cmd = ["integrate",
               "--valuation=integrate", self.algorithm,
               "--monomials=" + polynomial_file,
               polytope_file]

        with open(output_file, 'w') as f:
            return_value = call(cmd, stdout=f, stderr=f)

        """
        if return_value != 0:
            msg = "LattE returned with status {}"
            print(msg.format(return_value))
            # LattE returns an exit status != 0 if the polytope is empty.
            # In the general case this may happen, raising an exception
            # is not a good idea.
            #raise WMIRuntimeException(msg.format(return_value))
        """
