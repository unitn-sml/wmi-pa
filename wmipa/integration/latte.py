__version__ = "0.999"
__author__ = "Paolo Morettin"

from fractions import Fraction
from functools import reduce
import numpy as np
import os
from shutil import which
from subprocess import call
from tempfile import TemporaryDirectory

LATTE_INSTALLED = which("integrate") is not None


class LattEIntegrator:
    """This class is a wrapper for the LattE integrator.
    It computes the exact integral of a polynomial over a convex polytope.
    """

    ALG_TRIANGULATE = "--triangulate"
    ALG_CONE_DECOMPOSE = "--cone-decompose"
    DEF_ALGORITHM = ALG_CONE_DECOMPOSE
    ALGORITHMS = [ALG_TRIANGULATE, ALG_CONE_DECOMPOSE]

    _POLYNOMIAL_FILENAME = 'polynomial.txt'
    _POLYTOPE_FILENAME = 'polytope.hrep'
    _OUTPUT_FILENAME = 'output.txt'

    def __init__(self, algorithm=DEF_ALGORITHM):
        if not LATTE_INSTALLED:
            raise RuntimeError("Can't execute LattE's 'integrate' command.")
        if algorithm not in LattEIntegrator.ALGORITHMS:
            raise ValueError(f"Algorithm should be one of {ALGORITHMS}.")
        self.algorithm = algorithm

    def integrate(self, polytope, polynomial):

        with TemporaryDirectory(dir=".") as tmpdir:
            polytope_path = os.path.abspath(os.path.join(tmpdir, self._POLYTOPE_FILENAME))
            polynomial_path = os.path.abspath(os.path.join(tmpdir, self._POLYNOMIAL_FILENAME))
            output_path = os.path.abspath(os.path.join(tmpdir, self._OUTPUT_FILENAME))
            LattEIntegrator._write_polytope_file(polytope, polytope_path)
            LattEIntegrator._write_polynomial_file(polynomial, polynomial_path)
            
            cmd = ["integrate", "--valuation=integrate", self.algorithm,
                   f"--monomials=" + polynomial_path, polytope_path,]

            with open(output_path, "w") as f:
                return_value = call(cmd, stdout=f, stderr=f)
                if return_value != 0:
                    print(f"LattE returned non-zero value: {return_value}")
                    # LattE returns an exit status != 0 if the polytope is empty.
                    # In the general case this may happen, raising an exception
                    # is not a good idea.
                    # TODO HANDLE THIS PROPERLY!!

                result = LattEIntegrator._read_output_file(output_path)

        if not result:
            raise RuntimeError("Unhandled error while executing LattE integrale.")
        return result


    def integrate_batch(self, convex_integrals):
        volumes = []
        for polytope, polynomial in convex_integrals:
            volumes.append(self.integrate(polytope, polynomial))

        return np.array(volumes)


    @staticmethod
    def _write_polynomial_file(polynomial, path):
        mono_str = []
        for exponents, coefficient in polynomial.monomials.items():
            exp_str = "[" + ",".join(str(e) for e in exponents) + "]"
            mono_str.append(f"[{coefficient}, {exp_str}]")

        with open(path, "w") as f:
            f.write("[" + ",".join(mono_str) + "]")

    @staticmethod
    def _write_polytope_file(polytope, path):        
        A, b = polytope.to_numpy()
        bA = np.concatenate((b.reshape(-1, 1), A), axis=1)

        f_den = np.vectorize(lambda x : Fraction(x).denominator)
        f_lcmm = lambda vec : reduce(np.lcm, vec)

        mult = np.apply_along_axis(f_lcmm, 1, f_den(bA))
        bA_int = (bA * mult[:, None]).astype(int)
        bAm_int = np.concatenate((bA_int[:,0].reshape(-1,1),
                                  -bA_int[:,1:]), axis=1)

        with open(path, "w") as f:
            f.write(f"{bA.shape[0]} {bA.shape[1]}\n")
            f.write("\n".join([" ".join(map(str, row))
                               for row in bAm_int]))

    def lcmm(args):

        def _gcd(a, b):
            while b:
                a, b = b, a % b
            return a
        
        def _lcm(a, b):
            return a * b // _gcd(a, b)
        
        return reduce(_lcm, args)

    @staticmethod
    def _read_output_file(path):
        res = None
        with open(path, "r") as f:
            lines = f.readlines()
            for line in lines:
                # Result in the "Answer" line may be written in fraction form
                if "Decimal" in line:
                    # print("Res: {}".format(line))
                    return float(line.partition(": ")[-1].strip())

            txtblock = '\n'.join(lines)
            if "The number of lattice points is 1." in txtblock:
                return 0
            elif "Empty polytope or unbounded polytope!" in txtblock:
                error = WMIIntegrationException.OTHER_ERROR
            elif "Cannot compute valuation for unbounded polyhedron." in txtblock:
                error = WMIIntegrationException.UNBOUNDED_POLYHEDRON
            else:
                # TODO: are we sure about this?
                error = WMIIntegrationException.MEMORY_LIMIT

            raise WMIIntegrationException(error)

        return res


