import re
import shutil
import time
from abc import abstractmethod
from fractions import Fraction
from multiprocessing import Manager, Pool
from subprocess import call
from tempfile import NamedTemporaryFile

from pysmt.shortcuts import LE, LT

from wmipa.integration.integrator import Integrator
from wmipa.integration.polytope import Polynomial
from wmipa.wmiexception import WMIRuntimeException


class CacheIntegrator(Integrator):
    """This class handles the integration of polynomials over (convex) polytopes, using caching and parallel
    computation.

    It currently implements two levels of caching (-1, 0):

     - Level -1:
        no caching
     - Level 0:
        * the problem key is defined as the tuple (polytope, integrand).
        * duplicates are recognized before the integrator is called.

    It inherits from the abstract class Integrator.

    Attributes:
        n_threads (int): The number of threads to use when integrating a batch of problems.
        stub_integrate (bool): If True, the values will not be computed (0 is returned)
        hashTable (ConcurrentHashTable): The concurrent hash table used for caching.
        parallel_integration_time (float): The time spent in integration, accounting for parallelization.
        sequential_integration_time (float): The time spent in integration, excluding parallelization (i.e., the sum
            of the times spent by each thread).
    """

    DEF_N_THREADS = 7

    def __init__(self, n_threads=DEF_N_THREADS, stub_integrate=False):
        """Default constructor.

        Args:
            n_threads: Defines the number of threads to use.
            stub_integrate: If True the integrals will not be computed

        """

        self.n_threads = n_threads
        self.stub_integrate = stub_integrate
        self.hashTable = ConcurrentHashTable()
        self.parallel_integration_time = 0.0
        self.sequential_integration_time = 0.0


    def _integrate_problem_or_cached(self, integrand, polytope, key, cache):
        value = self.hashTable.get(key)
        if value is not None:
            return value, True
        value = self._integrate_problem(integrand, polytope)
        if cache:
            self.hashTable.set(key, value)
        return value, False

    @abstractmethod
    def _integrate_problem(self, integrand, polytope) -> float:
        raise NotImplementedError() # implement this in the concrete subclass

    @staticmethod
    def _compute_key(polytope, integrand):
        variables = list(integrand.variables.union(polytope.variables))
        polytope_key = ConcurrentHashTable._polytope_key(polytope, variables)
        integrand_key = ConcurrentHashTable._integrand_key(integrand, variables)
        return (polytope_key, integrand_key)


    def integrate_batch(self, problems, cache, *args, **kwargs):
        """Integrates a batch of problems of the type {atom_assignments, weight, aliases}

        Args:
            problems (list(atom_assignments, weight, aliases)): The list of problems to
                integrate.
            cache (int): The level of caching to use (range -1, 0, 1, 2, 3).

        Returns:
            list(real): The list of integration results.
            int: The number of cached results.

        """
        start_time = time.time()
        EMPTY = -1

        problems_to_integrate = {}
        problem_id = []
        cached = 0
        for index, (atom_assignments, weight, aliases) in enumerate(problems):
            integrand, polytope = self._convert_to_problem(
                atom_assignments, weight, aliases
            )
            key = CacheIntegrator._compute_key(polytope, integrand)
            if polytope is not None and not polytope.is_empty():
                # cache >= 1 recognize duplicates before calling the integrator
                pid = key if cache >= 1 else index
                if pid not in problems_to_integrate:
                    problem = (
                        len(problems_to_integrate),
                        integrand,
                        polytope,
                        key,
                        cache >= 0,  # store the results in a hash table if cache >= 0
                    )
                    problems_to_integrate[pid] = problem
                else:
                    # duplicate found
                    cached += 1
                problem_id.append(problems_to_integrate[pid][0])
            else:
                problem_id.append(EMPTY)

        setup_time = time.time() - start_time
        start_time = time.time()
        problems_to_integrate = problems_to_integrate.values()
        assert len(problem_id) == len(problems)
        # Handle multithreading
        pool = Pool(self.n_threads)
        results = pool.map(self._integrate_wrapper, problems_to_integrate)
        pool.close()
        pool.join()
        values = [0.0 if pid == EMPTY else results[pid][0] for pid in problem_id]
        cached += sum([(pid == EMPTY) or results[pid][1] for pid in problem_id])

        self.sequential_integration_time += setup_time + sum([results[pid][2] for pid in problem_id])
        self.parallel_integration_time += setup_time + time.time() - start_time

        return values, cached


    def _integrate_wrapper(self, problem):
        """A wrapper to handle multithreading."""
        _, integrand, polytope, key, cache = problem
        start_time = time.time()
        value, cached = self._integrate_problem_or_cached(integrand, polytope, key, cache)
        total_time = time.time() - start_time
        return value, cached, total_time


    def integrate(self, atom_assignments, weight, aliases, cache):
        """Integrates a problem of the type {atom_assignments, weight, aliases}

        Args:
            atom_assignments (dict): Maps atoms to the corresponding truth value (True, False)
            weight (Weight): The weight function of the problem.
            aliases (dict): Alias relationship between variables.
            cache (int): The level of caching to use (range -1, 0, 1, 2, 3).


        Returns:
            real: The integration result.
            bool: True if the result was cached, False otherwise.

        """
        start_time = time.time()
        integrand, polytope = self._convert_to_problem(atom_assignments, weight, aliases)
        key = CacheIntegrator._compute_key(polytope, integrand)
        if polytope is None or polytope.is_empty():
            return 0.0, False
        value, cached = self._integrate_problem_or_cached(integrand, polytope, key, cache)
        integration_time = time.time() - start_time
        self.sequential_integration_time += integration_time
        self.parallel_integration_time += integration_time
        return value, cached

    @classmethod
    @abstractmethod
    def _make_problem(cls, weight, bounds, aliases):
        """Creates a problem of the type (integrand, polytope) from the given arguments.

        Args:
            weight (FNode): The weight of the integrand.
            bounds (list): The bounds of the polytope.
            aliases (dict): The aliases of the variables.

        Returns:
            integrand (Integrand): The problem to integrate.
            polytope (Polytope): The polytope to integrate over.

        """
        raise NotImplementedError() # implement this in the concrete subclass

    @classmethod
    def _convert_to_problem(cls, atom_assignments, weight, aliases):
        """Transforms an assignment into a problem, defined by:
            - a polynomial integrand
            - a convex polytope.

        Args:
            atom_assignments (dict): The assignment of the problem.
            weight (FNode): The weight of the problem.
            aliases (dict): The list of all the alias variables (like PI=3.14)

        Returns:
            integrand (Integrand): A representation of the weight.
            polytope (Polytope): The polytope representing the list of inequalities.

        """
        bounds = []
        for atom, value in atom_assignments.items():
            assert isinstance(value, bool), "Assignment value should be Boolean"

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

        return cls._make_problem(weight, bounds, aliases)


class ConcurrentHashTable:
    def __init__(self):
        manager = Manager()
        self.table = manager.dict()

    def get(self, key):
        try:
            return self.table.get(key)
        except TypeError as ex:
            print("ConcurrentHashTable error:\n", ex)
            return self.get(key)

    def set(self, key, value):
        self.table[key] = value

    @staticmethod
    def _polytope_key(polytope, variables):
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
        return polytope_key

    @staticmethod
    def _integrand_key(integrand, variables):
        if not isinstance(integrand, Polynomial):
            return integrand
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
        return integrand_key
