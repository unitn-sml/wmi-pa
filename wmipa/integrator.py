
from abc import ABC, abstractmethod
from fractions import Fraction
from multiprocessing import Manager, Pool
from os import chdir, getcwd
import re
from subprocess import call
from tempfile import NamedTemporaryFile, TemporaryDirectory
from pysmt.shortcuts import LT, LE
import time

from wmipa.polytope import Polynomial, Polytope
from wmipa.wmiexception import WMIRuntimeException


class Integrator(ABC):
    """This class represents the general integrator with which to compute integrals.

    For the moment there is only one integrator that uses LattE Integrale.

    """

    """Default constructor.

        Args:
            **options: whatever option is needed for the integrator

    """
    @abstractmethod
    def __init__(self, **options):
        pass

    """Integrates a problem of the type {atom_assignments, weight, aliases}

        Args:
            problem (atom_assignments, weight, aliases): The problem to integrate.

        Returns:
            real: The integration result.

    """
    @abstractmethod
    def integrate(self, atom_assignments, weight, aliases):
        pass

    """Integrates a batch of problems of the type {atom_assignments, weight, aliases}

        Args:
            problems (list(atom_assignments, weight, aliases)): The list of problems to integrate.

    """
    @abstractmethod
    def integrate_batch(self, problems):
        pass


class CommandLineIntegrator(Integrator):
    """This class handles the integration of polynomial functions over (convex) polytopes.
    It is a wrapper for an integrator that reads (writes) input (output) from (to) file.
    It implements different levels of caching (-1, 0, 1, 2, 3).

    It inherits from the abstract class Integrator.

    Attributes:
        algorithm (str): The algorithm to use when computing the integrals.
        n_threads (int): The number of threads to use.
        stub_integrate (bool): If True, the values will not be computed (0 is returned)
    """
    DEF_ALGORITHM = None
    ALGORITHMS = []

    DEF_N_THREADS = 7

    # Template name for the temporary folder
    FOLDER_TEMPLATE = "tmp_{}"

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
                - stub_integrate: If True the integrals will not be computed

        """
        # get algorithm
        algorithm = options.get('algorithm')
        self.algorithm = algorithm or self.DEF_ALGORITHM

        # check that algorithm exists
        if self.algorithm not in self.ALGORITHMS:
            err = '{}, choose one from: {}'.format(
                self.algorithm, ', '.join(self.ALGORITHMS))
            raise WMIRuntimeException(WMIRuntimeException.INVALID_MODE, err)

        # set threads
        n_threads = options.get('n_threads')
        self.n_threads = n_threads or self.DEF_N_THREADS

        self.hashTable = HashTable()
        stub_integrate = options.get('stub_integrate')
        self.stub_integrate = stub_integrate or False
        self.integration_time = 0.0

    def get_integration_time(self):
        return self.integration_time

    def integrate_batch(self, problems, cache):
        """Integrates a batch of problems of the type {atom_assignments, weight, aliases}

        Args:
            problems (list(atom_assignments, weight, aliases)): The list of problems to integrate.

        """

        if cache <= 0:
            # Convert the problems into (integrand, polytope)
            for index in range(len(problems)):
                atom_assignments, weight, aliases, cond_assignments = problems[index]
                integrand, polytope = self._convert_to_problem(
                    atom_assignments, weight, aliases)
                problems[index] = (
                    integrand, polytope, cond_assignments, cache == 0)

            # Handle multithreading
            start_time = time.time()
            pool = Pool(self.n_threads)
            results = pool.map(self.integrate_wrapper, problems)
            values = [r[0] for r in results]
            cached = len([r[1] for r in results if r[1] > 0])
            pool.close()
            pool.join()
            self.integration_time = time.time() - start_time
            return values, cached
        elif cache == 1 or cache == 2 or cache == 3:
            unique_problems = {}
            cached_before = 0
            problems_to_integrate = []
            for index in range(len(problems)):
                # get problem
                atom_assignments, weight, aliases, cond_assignments = problems[index]

                # convert to integrator format
                integrand, polytope = self._convert_to_problem(
                    atom_assignments, weight, aliases)

                # get hash key
                variables = list(integrand.variables.union(polytope.variables))
                if cache == 3:
                    polytope = self._remove_redundancy(polytope)
                    if polytope is None:
                        continue
                if cache == 2 or cache == 3:
                    key = self.hashTable.key_2(polytope, integrand)
                else:
                    key = self.hashTable.key(
                        polytope, cond_assignments, variables)

                # add to unique
                if key not in unique_problems:
                    unique_problems[key] = {
                        "integrand": integrand,
                        "polytope": polytope,
                        "key": key,
                        "count": 1
                    }
                # else:
                #     cached_before += 1
                problems_to_integrate.append(unique_problems[key])

            # unique_problems = list(unique_problems.values())

            # Handle multithreading
            pool = Pool(self.n_threads)
            results = pool.map(
                self._integrate_problem_2,
                problems_to_integrate)
            values = [r[0] for r in results]
            cached = len([r[1] for r in results if r[1] > 0])
            pool.close()
            pool.join()

            return values, cached + cached_before
        else:
            raise Exception("Not implemented yet")

    def integrate_wrapper(self, problem):
        """A wrapper to handle multithreading."""
        integrand, polytope, cond_assignments, cache = problem
        return self._integrate_problem(
            integrand, polytope, cond_assignments, cache)

    def integrate(
            self,
            atom_assignments,
            weight,
            aliases,
            cond_assignments,
            cache):
        """Integrates a problem of the type {atom_assignments, weight, aliases}

        Args:
            problem (atom_assignments, weight, aliases): The problem to integrate.

        Returns:
            real: The integration result.

        """
        integrand, polytope = self._convert_to_latte(
            atom_assignments, weight, aliases)
        return self._integrate_problem(
            integrand, polytope, cond_assignments, cache)

    def _convert_to_problem(self, atom_assignments, weight, aliases):
        """Transforms an assignment into a problem, defined by:
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
            assert(isinstance(value, bool)), "Assignment value should be Boolean"

            # Skip atoms without variables
            if len(atom.get_free_variables()) == 0:
                continue

            if value is False:
                # If the negative literal is an inequality, change its
                # direction
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

    def _integrate_problem(self, integrand, polytope, cond_assignments, cache):
        """Generates the input files and calls integrator executable
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
            polynomial_file = self.POLYNOMIAL_TEMPLATE
            polytope_file = self.POLYTOPE_TEMPLATE
            output_file = self.OUTPUT_TEMPLATE

            # Change the CWD
            original_cwd = getcwd()
            chdir(folder)

            # Variable ordering is relevant in LattE files
            variables = sorted(integrand.variables.union(polytope.variables))

            # Write integrand and polytope to file
            self._write_polynomial_file(integrand, variables, polynomial_file)
            polytope_key = self._write_polytope_file(
                polytope, variables, polytope_file)
            key = tuple([polytope_key, cond_assignments])

            if cache:
                value = self.hashTable.get(key)
                if value is not None:
                    chdir(original_cwd)
                    return value, 1

            # Integrate and dump the result on file
            self._call_integrator(polynomial_file, polytope_file, output_file)

            # Read back the result and return to the original CWD
            result = self._read_output_file(output_file)
            chdir(original_cwd)

            if cache:
                self.hashTable.set(key, result)

            return result, 0

    def _integrate_problem_2(self, problem):
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
            return value * count, 1

        integrand = problem["integrand"]
        polytope = problem["polytope"]

        # Create a temporary folder containing the input and output files
        # possibly removing an older one
        with TemporaryDirectory(dir=".") as folder:

            polynomial_file = self.POLYNOMIAL_TEMPLATE
            polytope_file = self.POLYTOPE_TEMPLATE
            output_file = self.OUTPUT_TEMPLATE

            # Change the CWD
            original_cwd = getcwd()
            chdir(folder)

            # Variable ordering is relevant in LattE files
            variables = sorted(integrand.variables.union(polytope.variables))

            # Write integrand and polytope to file
            self._write_polynomial_file(integrand, variables, polynomial_file)
            self._write_polytope_file_2(polytope, variables, polytope_file)

            # Integrate and dump the result on file
            self._call_integrator(polynomial_file, polytope_file, output_file)

            # Read back the result and return to the original CWD
            result = self._read_output_file(output_file)
            chdir(original_cwd)

            self.hashTable.set(key, result)

            return result * count, 0

    def _read_output_file(self, path):
        """Reads the output file generated by the computation of the integrator.

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
        """Writes the polynomial into a file from where the integrator will read.

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
        """Writes the polytope into a file from where the integrator will read.

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
        with open(path, 'w') as f:
            f.write(latte_repr)

        bounds_key = sorted(bounds_key)
        return tuple(bounds_key)

    def _write_polytope_file_2(self, polytope, variables, path):
        """Writes the polytope into a file from where the integrator will read.

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
        with open(path, 'w') as f:
            f.write(latte_repr)

    @abstractmethod
    def _call_integrator(self, polynomial_file, polytope_file, output_file):
        pass

    def _remove_redundancy(self, polytope):
        polytope.bounds = list(set(polytope.bounds))
        polytope, internal_point = self._preprocess(polytope)
        if polytope is None:
            return None
        non_redundant_index = []
        to_analyze = list(range(0, len(polytope.bounds)))
        while (len(to_analyze) > 0):
            index = to_analyze[0]
            non_redundant, essential_index = self._clarkson(
                polytope, internal_point, non_redundant_index, index)
            if non_redundant:
                non_redundant_index.append(essential_index)
            to_analyze.remove(essential_index)
        non_redundant_bounds = [polytope.bounds[i]
                                for i in non_redundant_index]
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

        obj = [0] * len(variables) + [1]
        A = []
        b = []
        for bound in polytope.bounds:
            a = [0] * len(variables) + [1]
            for var_name in bound.coefficients:
                var_index = variables.index(var_name)
                a[var_index] = bound.coefficients[var_name]
            A.append(a)
            b.append(bound.constant)

        # x_0 <= 1
        A.append([0] * len(variables) + [1])
        b.append(1)

        optimal_value, optimal_solution = self._lp(A, b, obj, "maximize")

        # remove x_0
        optimal_solution = optimal_solution[:-1]

        if optimal_value > 0:
            # polytope dimension = len(variables)
            return polytope, optimal_solution
        elif optimal_value < 0:
            # polytope empty
            return None, []
        else:
            # polytope neither full-dimensional nor empty
            # TODO ?
            return polytope, optimal_solution

    def _clarkson(
            self,
            polytope,
            internal_point,
            non_redundant_index,
            index_to_check):
        """
            maximize A_k*x
            subject to:
                A_i*x <= b_i        for all i in I - k
                A_k*x <= b_k +1

            non redundant if optimal solution > b_k
        """
        variables = list(polytope.variables)
        obj = []
        A = []
        b = []
        b_k = None

        for i, bound in enumerate(polytope.bounds):
            if i == index_to_check or i in non_redundant_index:
                a = [0] * len(variables)
                for var_name in bound.coefficients:
                    var_index = variables.index(var_name)
                    a[var_index] = bound.coefficients[var_name]
                A.append(a)
                b_i = bound.constant
                if i == index_to_check:
                    b_k = b_i
                    b_i += 1
                    obj = [1 * v for v in a]
                b.append(b_i)
        assert b_k is not None

        optimal_value, optimal_solution = self._lp(A, b, obj, "maximize")

        non_redundant = optimal_value > b_k

        if non_redundant:
            return True, self._ray_shoot(
                polytope, internal_point, optimal_solution, index_to_check)
        else:
            return False, index_to_check

    def _get_truth_values(self, polytope, point):
        values = []
        variables = list(polytope.variables)

        assert len(point) == len(variables)

        for index, bound in enumerate(polytope.bounds):
            coefficients = [0] * len(variables)
            for var_name in bound.coefficients:
                var_index = variables.index(var_name)
                coefficients[var_index] = bound.coefficients[var_name]
            polynomial = [point[i] * coefficients[i]
                          for i in range(len(point))]
            truth_value = sum(polynomial) <= bound.constant
            values.append(truth_value)
        return values

    def _ray_shoot(self, polytope, start_point, end_point, index):
        values = self._get_truth_values(polytope, end_point)
        others = values[:index] + values[index + 1:]

        # if at the end point (optimal) there is only one disequalities falsified
        # then return that particular disequality (index)
        if min(others) == max(others):
            return index
        try:
            return self._ray_shoot_iter(polytope, start_point, end_point)
        except RecursionError:
            print("RECURSION")
            return index

    def _ray_shoot_iter(self, polytope, start_point, end_point):
        # start point is inside the polytope so every bound is respected
        # calculate middle point
        assert len(start_point) == len(end_point)
        middle_point = [((end_point[i] + start_point[i]) * Fraction(1, 2))
                        for i in range(len(start_point))]

        # check bounds
        intersected = None
        values = self._get_truth_values(polytope, middle_point)

        for i, v in enumerate(values):
            if not v:
                if intersected is None:
                    intersected = i
                else:
                    intersected = -1
                    break

        if intersected is None:
            return self._ray_shoot_iter(polytope, middle_point, end_point)
        elif intersected < 0:
            return self._ray_shoot_iter(polytope, start_point, middle_point)
        else:
            return intersected

    def _lp(self, A, B, obj, type_="maximize"):
        f = NamedTemporaryFile(mode='w+t', dir=("."))

        assert len(A) == len(B)

        variable_names = [("x_{}".format(i)) for i in range(len(A[0]))]

        # needed to retrieve the values
        f.writelines("(set-option :produce-models true)")

        # declare all variables
        for var in variable_names:
            f.writelines("(declare-fun {} () Real)".format(var))

        # add all constraints
        f.writelines("(assert (and")
        for i in range(len(A)):
            a = A[i]
            b = B[i]
            assert len(a) == len(variable_names)
            coeffs = []
            for c in a:
                if c < 0:
                    coeffs += ["(- {})".format(abs(c))]
                else:
                    coeffs += [str(c)]
            assert len(a) == len(coeffs)
            b = str(b) if b >= 0 else "(- {})".format(abs(b))
            monomials = [("(* {} {})".format(coeffs[j], variable_names[j]))
                         for j in range(len(a))]
            if len(monomials) > 1:
                constraint = "(<= (+ {}) {})".format(" ".join(monomials), b)
            else:
                constraint = "(<= {} {})".format(monomials[0], b)
            f.writelines(constraint)
        f.writelines("))")

        # add objective
        coeffs = []
        for c in obj:
            if c < 0:
                coeffs += ["(- {})".format(abs(c))]
            else:
                coeffs += [str(c)]
        monomials = [("(* {} {})".format(coeffs[j], variable_names[j]))
                     for j in range(len(obj))]
        if len(monomials) > 1:
            f.writelines("({} (+ {}))".format(type_, " ".join(monomials)))
        else:
            f.writelines("({} {})".format(type_, monomials[0]))

        f.writelines("(check-sat)")
        f.writelines("(get-objectives)")
        f.writelines("(load-objective-model 1)")
        for var in variable_names:
            f.writelines("(get-value ({}))".format(var))
        f.writelines("(exit)")
        f.seek(0)

        # read output
        values = []
        out = NamedTemporaryFile(mode='w+t', dir=("."))
        output = call(["optimathsat", f.name], stdout=out)
        out.seek(0)
        output = out.read()
        for line in output.split('\n'):
            """
                output can have these forms:
                    ( (x_N DIGITS) )
                    ( (x_N (- DIGITS)) )
                    ( (x_N (/ DIGITS DIGITS)) )
                    ( (x_N (- (/ DIGITS DIGITS))) )

                regex below is x_N + OR of the four different types
            """
            r = re.search(
                r'\( \(x_(\d+) (?:(\d+)|(?:\(- (\d+)\))|(?:\(\/ (\d+) (\d+)\))|(?:\(- \(\/ (\d+) (\d+)\)\)))\) \)',
                line)
            if r:
                var_index = r.group(1)
                if r.group(2):
                    values.append(Fraction(int(r.group(2))))
                elif r.group(3):
                    values.append(-1 * Fraction(int(r.group(3))))
                elif r.group(4):
                    values.append(Fraction(int(r.group(4)), int(r.group(5))))
                elif r.group(6):
                    values.append(-1 * Fraction(int(r.group(6)),
                                  int(r.group(7))))

        assert len(values) == len(variable_names)
        obj_value = sum([(obj[i] * values[i]) for i in range(len(values))])
        return obj_value, values


class HashTable:

    def __init__(self):
        manager = Manager()
        self.table = manager.dict()

    def get(self, key):
        try:
            return self.table.get(key)
        except TypeError as ex:
            print("HashTable error:\n", ex)
            return self.get(key)

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
