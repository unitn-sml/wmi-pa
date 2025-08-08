# WMI-PA

[![Build and Test (Python 3.9+, macOS, Linux)](https://github.com/unitn-sml/wmi-pa/actions/workflows/build-and-test.yml/badge.svg)](https://github.com/unitn-sml/wmi-pa/actions/workflows/build-and-test.yml)
[![codecov](https://codecov.io/github/unitn-sml/wmi-pa/branch/featherweight/graph/badge.svg?token=VIN9CAWNZP)](https://codecov.io/github/unitn-sml/wmi-pa)

Python 3 implementation of the methods presented in:

[Efficient WMI via SMT-Based Predicate Abstraction](https://www.ijcai.org/proceedings/2017/100)  
Paolo Morettin, Andrea Passerini, Roberto Sebastiani,  
in Proceedings of IJCAI 2017

[Advanced smt techniques for Weighted Model Integration](https://www.sciencedirect.com/science/article/abs/pii/S0004370219301213)  
Paolo Morettin, Andrea Passerini, Roberto Sebastiani,  
in Artificial Intelligence, Volume 275, 2019

[SMT-based Weighted Model Integration with Structure Awareness](https://arxiv.org/abs/2206.13856)  
Giuseppe Spallitta, Gabriele Masina, Paolo Morettin, Andrea Passerini, Roberto Sebastiani,  
in UAI Conference 2022

[Enhancing SMT-based Weighted Model Integration by structure awareness](https://www.sciencedirect.com/science/article/pii/S0004370224000031)  
Giuseppe Spallitta, Gabriele Masina, Paolo Morettin, Andrea Passerini, Roberto Sebastiani,  
in Artificial Intelligence, Volume 328, 2024

## Installation

Base version:

```bash
pip install wmipa
```

### Additional requirements

WMI-PA comes installed with a default enumerator (based on the `z3` SMT-solver) and a default integration backend (based
on rejection-sampling).

To use the most up-to-date algorithms, however, you need to install additional requirements.
The script `wmipa install` can be used to install all the requirements automatically on Unix-like systems (Linux,
macOS).
For Windows users, see the section below for specific instructions.

```
usage: wmipa install [-h] [--msat] [--nra] [--latte] [--all] [--install-path INSTALL_PATH] [--assume-yes] [--force-reinstall] [--include-path INCLUDE_PATH] [--lib-path LIB_PATH] [--cxx CXX]

options:
  -h, --help            show this help message and exit
  --msat                Install MathSAT
  --nra                 Install PySMT version with NRA support
  --latte               Install LattE Integrale
  --all                 Install all dependencies
  --install-path INSTALL_PATH
                        Install path for external tools
  --assume-yes, -y      Automatic yes to prompts
  --force-reinstall, -f
                        Force reinstallation of dependencies
  --include-path INCLUDE_PATH
                        Additional include paths for compilation (can be specified multiple times)
  --lib-path LIB_PATH   Additional library paths for compilation (can be specified multiple times)
  --cxx CXX             C++ compiler to use
```

E.g., for using the latest `SAE4WMI` enumeration algorithm, you should install the `MathSAT5` SMT solver.
For an exact integration backend, you should install the `LattE integrale` library.

To install these requirements, you can run the following command:

```bash
wmipa install --msat --latte --assume-yes
````

Then, a message will be shown to add the following lines to the `~/.bashrc` file:

```
PATH=$HOME/.wmipa/latte/bin:$PATH
```

#### Windows users

The `wmipa install` script is not directly supported on Windows.
We recommend using the Windows Subsystem for Linux (WSL) to run the script.

## Examples

We provide some examples that show how to write a model and evaluate weighted model integrals on it.
To run the code in *examples/*, type:

    python exampleX.py

## Command line interface

WMI-PA provides a command line interface to run WMI queries on models.
See `wmipa run --help` for more information:

```bash
usage: wmipa run [-h] [--enumerator ENUMERATOR] [--integrator INTEGRATOR] [--n_processes N_PROCESSES] [--n_samples N_SAMPLES] [--seed SEED] filename

positional arguments:
  filename              Path to the input density file

options:
  -h, --help            show this help message and exit
  --enumerator ENUMERATOR
                        Enumerator
  --integrator INTEGRATOR
                        Integrator
  --n_processes N_PROCESSES
                        # processes (for parallel integrators)
  --n_samples N_SAMPLES
                        # samples (for MC-based integrators)
  --seed SEED           seed (for randomized integrators)
```

## Experiments

The code for running the experiments reported in the papers above can be found in the `experiments` branch.
