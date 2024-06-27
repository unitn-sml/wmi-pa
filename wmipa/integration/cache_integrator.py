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
    """This class handles the integration of polynomials over (convex)
    polytopes, using caching and parallel computation.

    It currently implements two levels of caching (-1, 0):

     - Level -1:
        no caching
     - Level 0:
        * the problem key is defined as the tuple (polytope, integrand).
        * duplicates are recognized before the integrator is called.

    Attributes:

        n_threads (int): The number of threads to use when integrating
            a batch of problems.

        stub_integrate (bool): If True, the values will not be
            computed (0 is returned) hashTable (ConcurrentHashTable):
            The concurrent hash table used for caching.

        parallel_runtime (float): Integration runtime.

        sequential_runtime (float): Runtime without parallelization.

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
        self.parallel_runtime = 0.0
        self.sequential_runtime = 0.0

    def _integrate_with_cache(self, integrand, polytope, key, cache):
        value = self.hashTable.get(key)
        if value is not None:
            return value, True
        value = self._compute_integral(integrand, polytope)
        if cache:
            self.hashTable.set(key, value)
        return value, False

    @abstractmethod
    def _compute_integral(self, integral, polytope) -> float:
        raise NotImplementedError() # implement this in the concrete subclass

    @staticmethod
    def _compute_key(polytope, integrand):
        variables = list(integrand.variables.union(polytope.variables))
        polytope_key = ConcurrentHashTable._polytope_key(polytope, variables)
        integrand_key = ConcurrentHashTable._integrand_key(integrand, variables)
        return (polytope_key, integrand_key)


    def integrate_batch(self, integrals, cache, *args, **kwargs):
        """Integrates a list of (polytope, integrand)

        Args:
            integrals (list(Polytope, Integrand)).

        Returns:
            list(real): The list of integrals.
            int: The number of cache hits.

        """
        start_time = time.time()
        EMPTY = -1

        integrals_to_integrate = {}
        problem_id = []
        cached = 0
        for index, (polytope, integrand) in enumerate(integrals):
            key = CacheIntegrator._compute_key(polytope, integrand)
            if polytope is not None and not polytope.is_empty():
                # cache >= 1 recognize duplicates before calling the integrator
                pid = key if cache >= 1 else index
                if pid not in integrals_to_integrate:
                    problem = (
                        len(integrals_to_integrate),
                        integrand,
                        polytope,
                        key,
                        cache >= 0,  # store the results in a hash table if cache >= 0
                    )
                    integrals_to_integrate[pid] = problem
                else:
                    # duplicate found
                    cached += 1
                problem_id.append(integrals_to_integrate[pid][0])
            else:
                problem_id.append(EMPTY)

        setup_time = time.time() - start_time
        start_time = time.time()
        integrals_to_integrate = integrals_to_integrate.values()
        assert len(problem_id) == len(integrals)
        # Handle multithreading
        pool = Pool(self.n_threads)
        results = pool.map(self._integrate_wrapper, integrals_to_integrate)
        pool.close()
        pool.join()
        values = [0.0 if pid == EMPTY else results[pid][0] for pid in problem_id]
        cached += sum([(pid == EMPTY) or results[pid][1] for pid in problem_id])

        self.sequential_runtime += setup_time + sum([0 if pid == EMPTY else results[pid][2] for pid in problem_id])
        self.parallel_runtime += setup_time + time.time() - start_time

        return values, cached


    def _integrate_wrapper(self, integral):
        """A wrapper to handle multithreading."""
        _, integrand, polytope, key, cache = integral
        start_time = time.time()
        value, cached = self._integrate_with_cache(integrand, polytope, key, cache)
        total_time = time.time() - start_time
        return value, cached, total_time


    def integrate(self, polytope, integrand, cache):
        """Integrates a single (polytope, integrand)

        Args:
            polytope (Polytope): A polytope (H-representation).
            integrand (Integrand): The integrand function.

        Returns:
            real: The integration result.
            bool: Was the result in cache?.

        """
        start_time = time.time()
        key = CacheIntegrator._compute_key(polytope, integrand)
        if polytope is None or polytope.is_empty():
            return 0.0, False
        value, cached = self._integrate_with_cache(integrand, polytope, key, cache)
        runtime = time.time() - start_time
        self.sequential_runtime += runtime
        self.parallel_runtime += runtime
        return value, cached


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
