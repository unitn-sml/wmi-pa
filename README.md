# WMI-PA

[![Build and Test (Python 3.9+, macOS, Linux)](https://github.com/unitn-sml/wmi-pa/actions/workflows/build-and-test.yml/badge.svg)](https://github.com/unitn-sml/wmi-pa/actions/workflows/build-and-test.yml)
[![codecov](https://codecov.io/github/unitn-sml/wmi-pa/branch/featherweight/graph/badge.svg?token=VIN9CAWNZP)](https://codecov.io/github/unitn-sml/wmi-pa)

Python 3 implementation of the methods presented in:

[1] [Efficient WMI via SMT-Based Predicate Abstraction](https://www.ijcai.org/proceedings/2017/100)  
Paolo Morettin, Andrea Passerini, Roberto Sebastiani,  
in Proceedings of IJCAI 2017

[2] [Advanced smt techniques for Weighted Model Integration](https://www.sciencedirect.com/science/article/abs/pii/S0004370219301213)  
Paolo Morettin, Andrea Passerini, Roberto Sebastiani,  
in Artificial Intelligence, Volume 275, 2019

[3] [SMT-based Weighted Model Integration with Structure Awareness](https://arxiv.org/abs/2206.13856)  
Giuseppe Spallitta, Gabriele Masina, Paolo Morettin, Andrea Passerini, Roberto Sebastiani,  
in UAI Conference 2022

[4] [Enhancing SMT-based Weighted Model Integration by structure awareness](https://www.sciencedirect.com/science/article/pii/S0004370224000031)  
Giuseppe Spallitta, Gabriele Masina, Paolo Morettin, Andrea Passerini, Roberto Sebastiani,  
in Artificial Intelligence, Volume 328, 2024

## Installation

The package can be installed using `pip`:

```bash
pip install wmipa
```

WMI-PA comes installed with:

- a default enumerator (based on the [z3 SMT-solver](https://github.com/Z3Prover/z3))
- a default integration backend (approximated, based on rejection-sampling).

### Additional requirements

**_To use the most up-to-date algorithms, you need to install additional requirements._**

The script `wmipa install` can be used to install the requirements on Unix-like systems (Linux,
macOS).
For Windows users, see the section below.

```
usage: wmipa install [-h] [--msat] [--nra] [--latte] [--all] [--install-path INSTALL_PATH] [--assume-yes] [--force-reinstall] [--include-path INCLUDE_PATH] [--lib-path LIB_PATH] [--cxx CXX]

options:
  -h, --help            show this help message and exit
  --msat                Install MathSAT (default: False)
  --nra                 Install PySMT version with NRA support (default: False)
  --latte               Install LattE Integrale (default: False)
  --all                 Install all dependencies (default: False)
  --install-path INSTALL_PATH
                        Install path for external tools (default: /home/gabriele/.wmipa)
  --assume-yes, -y      Automatic yes to prompts (default: False)
  --force-reinstall, -f
                        Force reinstallation of dependencies (default: False)
  --include-path INCLUDE_PATH
                        Additional include paths for compilation (can be specified multiple times) (default: ['/usr/local/include'])
  --lib-path LIB_PATH   Additional library paths for compilation (can be specified multiple times) (default: ['/usr/local/lib'])
  --cxx CXX             C++ compiler to use (default: g++)
```

E.g., for using the latest `SAE4WMI` enumeration algorithm [4], you should install
the [MathSAT5 SMT-solver](https://mathsat.fbk.eu/) API.
For an exact integration backend, you should install the [LattE integrale](https://github.com/latte-int/latte/) library.

To install these requirements, you can run:

```bash
wmipa install --msat --latte --assume-yes
````

Follow the instructions to install the required dependencies, and
to update your `PATH` environment variable if necessary, e.g., by setting it in your shell configuration file as
follows:

```
PATH=$HOME/.wmipa/latte/bin:$PATH
```

#### Windows users

The `wmipa install` script is not directly supported on Windows.
We recommend using the Windows Subsystem for Linux (WSL) to run the script.

## Usage

The library comes with a command line interface to run WMI queries on models, as well as a Python API
with algorithms and building blocks for computing WMI.

### Command line interface

```
usage: wmipa run [-h] [--enumerator ENUMERATOR] [--async_queue_size ASYNC_QUEUE_SIZE] [--integrator INTEGRATOR] [--n_processes N_PROCESSES] [--n_samples N_SAMPLES] [--seed SEED] filename

positional arguments:
  filename              Path to the input density file

options:
  -h, --help            show this help message and exit
  --enumerator ENUMERATOR
                        Enumerator (default: z3)
  --async_queue_size ASYNC_QUEUE_SIZE
                        Size of the async queue (for async enumerators) (default: None)
  --integrator INTEGRATOR
                        Integrator (latte, rejection, or wrapper form: axisaligned-..., cache-..., parallel-..., possibly composed) (default: rejection)
  --n_processes N_PROCESSES
                        Number of processes (for parallel integrators) (default: None)
  --n_samples N_SAMPLES
                        Number of samples (for MC-based integrators) (default: None)
  --seed SEED           seed (for randomized integrators) (default: None)
```

### API examples

In the `examples/` directory, you can find several examples of how to use the API.

## Experiments

The code for running the experiments reported in the papers above can be found in the `experiments` branch.
