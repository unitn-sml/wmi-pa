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
from scipy.optimize import linprog

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
        if cache <= 0:
            # Convert the problems into (integrand, polytope)
            for index in range(len(problems)):
                atom_assignments, weight, aliases, cond_assignments = problems[index]
                integrand, polytope = self._convert_to_latte(atom_assignments, weight, aliases)
                problems[index] = (integrand, polytope, cond_assignments, cache==0)
            
            # Handle multithreading
            pool = Pool(self.n_threads)
            results = pool.map(self.integrate_wrapper, problems)
            values = [r[0] for r in results]
            cached = len([r[1] for r in results if r[1] > 0])
            pool.close()
            pool.join()
            
            return values, cached
        elif cache == 1 or cache == 2 or cache == 3:
            # Convert the problems into (integrand, polytope)
            unique_problems = {}
            cached_before = 0
            for index in range(len(problems)):
                # get problem
                atom_assignments, weight, aliases, cond_assignments = problems[index]
                
                # convert to latte
                integrand, polytope = self._convert_to_latte(atom_assignments, weight, aliases)
                
                # get hash key
                variables = list(integrand.variables.union(polytope.variables))
                if cache == 2:
                    polytope = self._remove_redundancy(polytope)
                if cache == 3:
                    key = self.hashTable.key_2(polytope, integrand)
                else:
                    key = self.hashTable.key(polytope, cond_assignments, variables)
                
                # add to unique
                if key not in unique_problems:
                    unique_problems[key] = {
                        "integrand":integrand,
                        "polytope":polytope,
                        "key":key,
                        "count":0
                    }
                else:
                    cached_before += 1
                unique_problems[key]["count"] += 1
            unique_problems = list(unique_problems.values())
            
            # Handle multithreading
            pool = Pool(self.n_threads)
            results = pool.map(self._integrate_latte_2, unique_problems)
            values = [r[0] for r in results]
            cached = len([r[1] for r in results if r[1] > 0])
            pool.close()
            pool.join()
            
            return values, cached+cached_before
        else:
            raise Exception("Not implemented yet")
        
    def integrate_wrapper(self, problem):
        """A wrapper to handle multithreading."""
        integrand, polytope, cond_assignments, cache = problem
        return self._integrate_latte(integrand, polytope, cond_assignments, cache)
            
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
            
    def _integrate_latte_2(self, problem):
        """
        {
            "integrand":integrand,
            "polytope":polytope,
            "key":key,
            "count":0
        }
        """
        
        key = problem["key"]
        count = problem["count"]
        
        value = self.hashTable.get(key)
        if value is not None:
            return value*count, 1
        
        integrand = problem["integrand"]
        polytope = problem["polytope"]
        
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
            self._write_polytope_file_2(polytope, variables, polytope_file)
            
            # Integrate and dump the result on file
            self._call_latte(polynomial_file, polytope_file, output_file)
            
            # Read back the result and return to the original CWD
            result = self._read_output_file(output_file)            
            chdir(original_cwd)
            
            self.hashTable.set(key, result)
            
            return result*count, 0
        
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
        
    def _write_polytope_file_2(self, polytope, variables, path):
        """Writes the polytope into a file from where LattE will read.
        
        Args:
            polytope (Polytope): The polytope of the integration.
            variables (list): The sorted list of all the variables involved in the integration.
            path (str): The path of the file to write.
        """
        # Create the string representation of the polytope (LattE format)
        n_ineq = str(len(polytope.bounds))
        n_vars = str(len(variables) + 1)
        latte_repr = "{} {}\n".format(n_ineq, n_vars)
        for index, bound in enumerate(polytope.bounds):
            latte_repr += str(bound.constant) + " "
            for var in variables:
                if var in bound.coefficients:
                    latte_repr += str(-bound.coefficients[var]) + " "
                else:
                    latte_repr += "0 "
            latte_repr += "\n"
            
        # Write the string on the file
        with open(path,'w') as f:
            f.write(latte_repr)

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
    
    def _remove_redundancy(self, polytope):
        polytope, internal_point = self._preprocess(polytope)
        non_redundant_index = []
        to_analyze = list(range(0, len(polytope.bounds)))
        while (len(to_analyze) > 0):
            index = to_analyze[0]
            non_redundant, essential_index = self._clarkson(polytope, internal_point, non_redundant_index, index)
            if non_redundant:
                non_redundant_index.append(essential_index)
            to_analyze.remove(essential_index)
        non_redundant_bounds = [polytope.bounds[i] for i in non_redundant_index]
        polytope.bounds = non_redundant_bounds
        return polytope
    
    def _preprocess(self, polytope):
        """
            maximize x_0
            subject to:
                Ax + 1x0 <= b
                x_0 <= 1
                
            x_0 is a new variable
            Ax <= b is the polytope
        """
        variables = list(polytope.variables)
        to_minimize = [0]*len(variables) + [-1]
        A = []
        b = []
        for bound in polytope.bounds:
            a = [0]*len(variables) + [1]
            for var_name in bound.coefficients:
                var_index = variables.index(var_name)
                a[var_index] = bound.coefficients[var_name]
            A.append(a)
            b.append(bound.constant)
        ranges = [(None, None) for _ in range(len(to_minimize))]
        
        res = linprog(to_minimize, A_ub=A, b_ub=b, bounds=ranges)
        x_0 = res.fun*-1;  # *-1 because its a maximize problem
        point = res.x[:-1] # remove x_0
        
        if x_0 > 0:
            # polytope dimension = len(variables)
            return polytope, point
        elif x_0 < 0:
            # polytope empty
            return polytope, []
        else:
            # polytope neither full-dimensional nor empty
            # TODO
            raise("Not implemented yet");
        
    def _clarkson(self, polytope, internal_point, non_redundant_index, index_to_check):
        """
            maximize A_k*x
            subject to:
                A_i*x <= b_i        for all i in I - k
                A_k*x <= b_k +1
            
            non redundant if optimal solution > b_k
        """
        variables = list(polytope.variables)
        to_minimize = []
        A = []
        b = []
        b_k = None
        
        for i, bound in enumerate(polytope.bounds):
            if i == index_to_check or i in non_redundant_index:
                a = [0]*len(variables)
                for var_name in bound.coefficients:
                    var_index = variables.index(var_name)
                    a[var_index] = bound.coefficients[var_name]
                A.append(a)
                b_i = bound.constant
                if i == index_to_check:
                    b_k = b_i
                    b_i += 1
                    to_minimize = [-1*v for v in a]
                b.append(b_i)
        ranges = [(None, None) for _ in range(len(variables))]
        res = linprog(to_minimize, A_ub=A, b_ub=b, bounds=ranges)
        optimal_value = res.fun*-1 # *-1 because its a maximize problem
        
        non_redundant = optimal_value > b_k
        if non_redundant:
            optimal_solution = res.x
            return True, self._ray_shoot(polytope, internal_point, optimal_solution)
        else:
            return False, index_to_check
            
    def _ray_shoot(self, polytope, start_point, end_point):
        # start point is inside the polytope so every bound is respected
        # calculate middle point
        assert len(start_point) == len(end_point)
        middle_point = [((end_point[i]+start_point[i])*0.5) for i in range(len(start_point))]
        
        # check bounds
        intersected = None
        variables = list(polytope.variables)
        for index, bound in enumerate(polytope.bounds):
            coefficients = [0] * len(variables)
            for var_name in bound.coefficients:
                var_index = variables.index(var_name)
                coefficients[var_index] = bound.coefficients[var_name]
            polynomial = [middle_point[i]*coefficients[i] for i in range(len(middle_point))]
            truth_value = sum(polynomial) <= bound.constant
            if not truth_value:
                if intersected is None:
                    intersected = index
                else:
                    intersected = -1
                    break
                
        if intersected is None:
            return self._ray_shoot(polytope, middle_point, end_point)
        elif intersected < 0:
            return self._ray_shoot(polytope, start_point, middle_point)
        else:
            return intersected
    
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
        
    def key(self, polytope, cond_assignment, variables):
        bounds_key = []
        for index, bound in enumerate(polytope.bounds):
            bound_key = []
            for var in variables:
                if var in bound.coefficients:
                    bound_key.append(bound.coefficients[var])
                else:
                    bound_key.append(0)
            bound_key.append(bound.constant)
            bounds_key.append(tuple(bound_key))
            
        bounds_key = tuple(sorted(bounds_key))
        
        key = tuple([bounds_key, cond_assignment])
        return key
        
    def key_2(self, polytope, integrand):
        variables = list(integrand.variables.union(polytope.variables))
        
        # polytope key
        polytope_key = []
        for index, bound in enumerate(polytope.bounds):
            bound_key = []
            for var in variables:
                if var in bound.coefficients:
                    bound_key.append(bound.coefficients[var])
                else:
                    bound_key.append(0)
            bound_key.append(bound.constant)
            polytope_key.append(tuple(bound_key))
            
        polytope_key = tuple(sorted(polytope_key))
        
        # integrand key
        integrand_key = []
        
        """def sort_monomial(mon):
            coeff = mon.coefficient
            exp = []
            for var in variables:
                if var in mon.exponents:
                    exp.append(str(mon.exponents[var]))
                else:
                    exp.append(str(0))
            return tuple([coeff]+[exp])"""
        
        monomials = integrand.monomials
        
        for mon in monomials:
            mon_key = [float(mon.coefficient)]
            for var in variables:
                if var in mon.exponents:
                    mon_key.append(float(mon.exponents[var]))
                else:
                    mon_key.append(0)
            integrand_key.append(tuple(mon_key))
            
        integrand_key = tuple(sorted(integrand_key))
        
        key = tuple([polytope_key, integrand_key])
        return key
