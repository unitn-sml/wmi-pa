__version__ = "0.999"
__author__ = "Paolo Morettin"

import os
import subprocess
from fractions import Fraction
from functools import reduce
from shutil import which
from tempfile import TemporaryDirectory
from typing import Collection

import numpy as np

from wmipa.datastructures import Polytope, Polynomial

LATTE_INSTALLED = which("integrate") is not None


class LattEIntegrator:
    """This class is a wrapper for the LattE integrator.
    It computes the exact integral of a polynomial over a convex polytope.
    """

    ALG_TRIANGULATE = "--triangulate"
    ALG_CONE_DECOMPOSE = "--cone-decompose"
    DEF_ALGORITHM = ALG_CONE_DECOMPOSE
    ALGORITHMS = [ALG_TRIANGULATE, ALG_CONE_DECOMPOSE]

    _POLYNOMIAL_FILENAME = "polynomial.txt"
    _POLYTOPE_FILENAME = "polytope.hrep"
    _OUTPUT_FILENAME = "output.txt"

    def __init__(self, algorithm: str = DEF_ALGORITHM):
        if not LATTE_INSTALLED:
            raise RuntimeError(
                "Can't execute LattE's 'integrate' command. Use 'wmipa-install --latte' to install it."
            )
        if algorithm not in LattEIntegrator.ALGORITHMS:
            raise ValueError(f"Algorithm should be one of {self.ALGORITHMS}.")
        self.algorithm = algorithm

    def integrate(self, polytope: Polytope, polynomial: Polynomial) -> float:

        with TemporaryDirectory(dir=".") as tmpdir:
            polytope_path = os.path.abspath(
                os.path.join(tmpdir, self._POLYTOPE_FILENAME)
            )
            polynomial_path = os.path.abspath(
                os.path.join(tmpdir, self._POLYNOMIAL_FILENAME)
            )
            output_path = os.path.abspath(os.path.join(tmpdir, self._OUTPUT_FILENAME))
            LattEIntegrator._write_polytope_file(polytope, polytope_path)
            LattEIntegrator._write_polynomial_file(polynomial, polynomial_path)

            cmd = [
                "integrate",
                "--valuation=integrate",
                self.algorithm,
                f"--monomials=" + polynomial_path,
                polytope_path,
            ]

            with open(output_path, "w") as f:
                process_output = subprocess.run(cmd, stdout=f, stderr=f, cwd=tmpdir)
                if process_output.returncode != 0:
                    raise RuntimeError(
                        f"LattE returned non-zero value: {process_output.returncode}"
                    )
                    # Unfortunately LattE returns an exit status != 0 if the polytope is empty.
                    # In the general case this may happen, raising an exception
                    # is not a good idea.
                    # TODO HANDLE THIS PROPERLY!!

                result = LattEIntegrator._read_output_file(output_path)

        if not result:
            raise RuntimeError("Unhandled error while executing LattE integrale.")
        return result

    def integrate_batch(
        self, convex_integrals: Collection[tuple[Polytope, Polynomial]]
    ) -> np.ndarray:
        volumes = []
        for polytope, polynomial in convex_integrals:
            volumes.append(self.integrate(polytope, polynomial))

        return np.array(volumes)

    @staticmethod
    def _write_polynomial_file(polynomial: Polynomial, path: str) -> None:
        mono_str = []
        for exponents, coefficient in polynomial.monomials.items():
            exp_str = "[" + ",".join(str(e) for e in exponents) + "]"
            mono_str.append(f"[{coefficient}, {exp_str}]")

        with open(path, "w") as f:
            f.write("[" + ",".join(mono_str) + "]")

    @staticmethod
    def _write_polytope_file(polytope: Polytope, path: str) -> None:
        A, b = polytope.to_numpy()
        bA = np.concatenate((b.reshape(-1, 1), A), axis=1)

        f_den = np.vectorize(lambda x: Fraction(x).denominator)
        f_lcmm = lambda vec: reduce(np.lcm, vec)

        mult = np.apply_along_axis(f_lcmm, 1, f_den(bA))
        bA_int = (bA * mult[:, None]).astype(int)
        bAm_int = np.concatenate((bA_int[:, 0].reshape(-1, 1), -bA_int[:, 1:]), axis=1)

        with open(path, "w") as f:
            f.write(f"{bA.shape[0]} {bA.shape[1]}\n")
            f.write("\n".join([" ".join(map(str, row)) for row in bAm_int]))

    @staticmethod
    def _read_output_file(path: str) -> float:
        res = None
        with open(path, "r") as f:
            lines = f.readlines()
            for line in lines:
                # Result in the "Answer" line may be written in fraction form
                if "Decimal" in line:
                    # print("Res: {}".format(line))
                    return float(line.partition(": ")[-1].strip())

            txt_block = "\n".join(lines)
            if "The number of lattice points is 1." in txt_block:
                return 0
            elif "Empty polytope or unbounded polytope!" in txt_block:
                error = "Empty or unbounded polytope"
            elif "Given polyhedron is unbounded!" in txt_block:
                error = "Unbounded polytope"
            else:
                error = "LattE reached an unexpected state (memory limit?)"

            raise RuntimeError(error + txt_block)
