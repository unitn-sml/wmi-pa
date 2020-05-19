__version__ = '0.999'
__author__ = 'Paolo Morettin'

from subprocess import call
from os import makedirs, chdir, getcwd
from os.path import isdir
from shutil import rmtree
from multiprocessing import Pool, Manager
from pysmt.typing import REAL
from pysmt.shortcuts import LT, LE
from tempfile import TemporaryDirectory

from wmipa.integrator import Integrator
from wmipa.polytope import Polynomial, Polytope
from wmipa.wmiexception import WMIRuntimeException

class Latte_Integrator(Integrator):
    """This class handles the integration of polynomial functions over (convex) polytopes.
    
    It inherits from the abstract class Integrator.

    LattE Integrale is required.
    
    Attributes:
        algorithm (str): The algorithm to use when computing the integrals.
        n_threads (int): The number of threads to use.

    """

    ALG_TRIANGULATE = "--triangulate"
    ALG_CONE_DECOMPOSE = "--cone-decompose"
    DEF_ALGORITHM = ALG_CONE_DECOMPOSE

    ALGORITHMS = [ALG_TRIANGULATE, ALG_CONE_DECOMPOSE]

    DEF_N_THREADS = 7

    # Template name for the temporary folder
    FOLDER_TEMPLATE = "latte_{}"
    
    # Temporary files
    POLYTOPE_TEMPLATE = "polytope.hrep.latte"
    POLYNOMIAL_TEMPLATE = "polynomial.latte"
    OUTPUT_TEMPLATE = "output.txt"

    def __init__(self, **options):
        """Default constructor.
        
        Args:
            **options:
                - algorithm: Defines the algorithm to use when integrating.
                - n_threads: Defines the number of threads to use.
        
        """
        # get algorithm
        algorithm = options.get('algorithm')
        self.algorithm = algorithm or Latte_Integrator.DEF_ALGORITHM
        
        # check that algorithm exists
        if not self.algorithm in Latte_Integrator.ALGORITHMS:
            err = '{}, choose one from: {}'.format(self.algorithm, ', '.join(Latte_Integrator.ALGORITHMS))
            raise WMIRuntimeException(WMIRuntimeException.INVALID_MODE, err)
            
        # set threads
        n_threads = options.get('n_threads')
        self.n_threads = n_threads or Latte_Integrator.DEF_N_THREADS
        
        self.hashTable = HashTable()
        
    def integrate_batch(self, problems, cache):
        """Integrates a batch of problems of the type {atom_assignments, weight, aliases}
        
        Args:
            problems (list(atom_assignments, weight, aliases)): The list of problems to integrate.
        
        """
        # Convert the problems into (integrand, polytope)
        for index in range(len(problems)):
            atom_assignments, weight, aliases, cond_assignments = problems[index]
            integrand, polytope = self._convert_to_latte(atom_assignments, weight, aliases)
            if polytope.is_empty():
                problems[index] = None
            else:
                problems[index] = (integrand, polytope, cond_assignments, cache)
        
        # Handle multithreading
        pool = Pool(self.n_threads)
        results = pool.map(self.integrate_wrapper, problems)
        values = [r[0] for r in results]
        cached = len([r[1] for r in results if r[1] > 0])
        pool.close()
        pool.join()
        
        return values, cached
        
    def integrate_wrapper(self, problem):
        """A wrapper to handle multithreading."""
        if problem is not None:
            integrand, polytope, cond_assignments, cache = problem
            return self._integrate_latte(integrand, polytope, cond_assignments, cache)
        else:
            return 0.0, 0
            
    def integrate(self, atom_assignments, weight, aliases, cond_assignments, cache):
        """Integrates a problem of the type {atom_assignments, weight, aliases}
        
        Args:
            problem (atom_assignments, weight, aliases): The problem to integrate.
        
        Returns:
            real: The integration result.
            
        """
        integrand, polytope = self._convert_to_latte(atom_assignments, weight, aliases)
        return self._integrate_latte(integrand, polytope, cond_assignments, cache)
        
    def _integrate_latte(self, integrand, polytope, cond_assignments, cache):
        """Generates the input files and calls LattE's "integrate" executable
            to calculate the integral. Then, reads back the result and returns it
            as a float.
        
        Args:
            integrand (Polynomial): The integrand of the integration.
            polytope (Polytope): The polytope of the integration.
                
        Returns:
            real: The integration result.    
        
        """
        # Create a temporary folder containing the input and output files
        # possibly removing an older one
        with TemporaryDirectory(dir=".") as folder:
            polynomial_file = Latte_Integrator.POLYNOMIAL_TEMPLATE
            polytope_file = Latte_Integrator.POLYTOPE_TEMPLATE
            output_file = Latte_Integrator.OUTPUT_TEMPLATE
            
            # Change the CWD
            original_cwd = getcwd()
            chdir(folder)
            
            # Variable ordering is relevant in LattE files 
            variables = list(integrand.variables.union(polytope.variables))
            variables.sort()
            
            # Write integrand and polytope to file
            self._write_polynomial_file(integrand, variables, polynomial_file)
            polytope_key = self._write_polytope_file(polytope, variables, polytope_file)
            key = tuple([polytope_key, cond_assignments])
            
            if cache:
                value = self.hashTable.get(key)
                if value is not None:
                    chdir(original_cwd)
                    return value, 1
            
            # Integrate and dump the result on file
            self._call_latte(polynomial_file, polytope_file, output_file)
            
            # Read back the result and return to the original CWD
            result = self._read_output_file(output_file)            
            chdir(original_cwd)
            
            if cache:
                self.hashTable.set(key, result)
            
            return result, 0
        
    def _convert_to_latte(self, atom_assignments, weight, aliases):
        """Transforms an assignment into a LattE problem, defined by:
            - a polynomial integrand
            - a convex polytope.
            
        Args:
            atom_assignments (dict): The assignment of the problem.
            weight (FNode): The weight of the problem.
            aliases (dict): The list of all the alias variables (like PI=3.14)
            
        Returns:
            integrand (Polynomial): The polynomial representing the weight.
            polytope (Polytope): The polytope representing the list of inequalities.
            
        """
        bounds = []
        for atom, value in atom_assignments.items():
            assert(isinstance(value,bool)), "Assignment value should be Boolean"
            
            # Skip atoms without variables
            if len(atom.get_free_variables()) == 0:
                continue
            
            if value is False:
                # If the negative literal is an inequality, change its direction
                if atom.is_le():
                    left, right = atom.args()
                    atom = LT(right, left)
                elif atom.is_lt():
                    left, right = atom.args()
                    atom = LE(right, left)
                    
            # Add a bound if the atom is an inequality
            if atom.is_le() or atom.is_lt():                    
                bounds.append(atom)

        integrand = Polynomial(weight, aliases)
        polytope = Polytope(bounds, aliases)
        
        return integrand, polytope

    def _read_output_file(self, path):
        """Reads the output file generated by the computation of LattE Integrale.
        
        Args:
            path (str): The path of the file to read.
            
        Returns:
            real: The result of the computation written in the file.
        
        """
        res = None
        
        with open(path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                # Result in the "Answer" line may be written in fraction form
                if "Decimal" in line:
                    return float(line.partition(": ")[-1].strip())

            # empty polytope
            res = 0.0

        return res
        
    def _write_polynomial_file(self, integrand, variables, path):
        """Writes the polynomial into a file from where LattE will read.
        
        Args:
            integrand (Polynomial): The integrand of the integration.
            variables (list): The sorted list of all the variables involved in the integration.
            path (str): The path of the file to write.
        
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
        with open(path, 'w') as f:
            f.write(latte_repr)

    def _write_polytope_file(self, polytope, variables, path):
        """Writes the polytope into a file from where LattE will read.
        
        Args:
            polytope (Polytope): The polytope of the integration.
            variables (list): The sorted list of all the variables involved in the integration.
            path (str): The path of the file to write.
        
        """
        # Create the string representation of the polytope (LattE format)
        n_ineq = str(len(polytope.bounds))
        n_vars = str(len(variables) + 1)
        bounds_key = []
        latte_repr = "{} {}\n".format(n_ineq, n_vars)
        for index, bound in enumerate(polytope.bounds):
            bound_key = [bound.constant]
            latte_repr += str(bound.constant) + " "
            for var in variables:
                if var in bound.coefficients:
                    latte_repr += str(-bound.coefficients[var]) + " "
                    bound_key.append(-bound.coefficients[var])
                else:
                    latte_repr += "0 "
                    bound_key.append(0)
            latte_repr += "\n"
            bounds_key.append(tuple(bound_key))
            
        # Write the string on the file
        with open(path,'w') as f:
            f.write(latte_repr)
            
        bounds_key = sorted(bounds_key)
        return tuple(bounds_key)

    def _call_latte(self, polynomial_file, polytope_file, output_file):
        """Calls LattE executable to calculate the integrand of the problem
            represented by the given files.
            
        Args:
            polynomial_file (str): The path where to find the file with the representation of the polynomial.
            polytope_file (str): The path where to find the file with representation of the polytope.
            output_file (str): The file where to write the result of the computation.
        
        """
        cmd = ["integrate",
               "--valuation=integrate", self.algorithm,
               "--monomials=" + polynomial_file,
               polytope_file]
        
        with open(output_file, 'w') as f:
            return_value = call(cmd, stdout=f, stderr=f)
            
            """
            if return_value != 0:
                msg = "LattE returned with status {}"
                # LattE returns an exit status != 0 if the polytope is empty.
                # In the general case this may happen, raising an exception
                # is not a good idea.
            """
    
    
        
class HashTable():

    def __init__(self):
        manager = Manager()
        self.table = manager.dict()
        
    def get(self, key):
        try:
            value = self.table[key]
            return value
        except KeyError:
            return None
        
    def set(self, key, value):
        self.table[key] = value
