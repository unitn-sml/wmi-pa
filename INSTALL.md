## Base installation

The package can be installed using `pip`:

```bash
pip install wmpy
```

wmpy comes installed with:

- a default enumerator (based on the [z3 SMT-solver](https://github.com/Z3Prover/z3))
- a default integration backend (approximate, based on rejection-sampling).

## Additional requirements

**_To use the most up-to-date algorithms, you need to install additional requirements._**

The command `wmpy install` can be used to install the requirements on Unix-like systems (Linux,
macOS). For Windows users, we recommend using the Windows Subsystem for Linux (WSL).

```
usage: wmpy install [-h] [--msat] [--latte] [--all] [--install-path INSTALL_PATH] [--assume-yes] [--force-reinstall] [--include-path INCLUDE_PATH] [--lib-path LIB_PATH] [--cxx CXX]

options:
  -h, --help            show this help message and exit
  --msat                Install MathSAT (default: False)
  --latte               Install LattE Integrale (default: False)
  --all                 Install all dependencies (default: False)
  --install-path INSTALL_PATH
                        Install path for external tools (default: $HOME/.wmpy)
  --assume-yes, -y      Automatic yes to prompts (default: False)
  --force-reinstall, -f
                        Force reinstallation of dependencies (default: False)
  --include-path INCLUDE_PATH
                        Additional include paths for compilation (can be specified multiple times) (default: ['/usr/local/include'])
  --lib-path LIB_PATH   Additional library paths for compilation (can be specified multiple times) (default: ['/usr/local/lib'])
  --cxx CXX             C++ compiler to use (default: g++)
```

E.g., for using the state-of-the-art Structure-Aware Enumerator (`SAEnumerator`), install
the [MathSAT5 SMT-solver](https://mathsat.fbk.eu/) API.
For an exact integration backend, install the [LattE integrale](https://github.com/latte-int/latte/) library.

To install these requirements, you can run:

```bash
wmpy install --msat --latte --assume-yes
````

Follow the instructions to install the required dependencies, and
to update your `PATH` environment variable if necessary, e.g., by setting it in your shell configuration file as
follows:

```
PATH=$HOME/.wmpy/latte/bin:$PATH
```

### Command line interface

The library comes with a command line interface to solve weighted model integration problems.

```
usage: wmpy run [-h] [--enumerator ENUMERATOR] [--async_queue_size ASYNC_QUEUE_SIZE] [--integrator INTEGRATOR] [--n_processes N_PROCESSES] [--n_samples N_SAMPLES] [--seed SEED] filename

positional arguments:
  filename              Path to the input density file

options:
  -h, --help            show this help message and exit
  --enumerator ENUMERATOR
                        Enumerator (msat, z3, or wrapper: async-..., possibly composed) (default: z3)
  --async_queue_size ASYNC_QUEUE_SIZE
                        Size of the async queue (for async enumerators) (default: None)
  --integrator INTEGRATOR
                        Integrator (latte, rejection, or wrapper: axisaligned-..., cache-..., parallel-..., possibly composed) (default: rejection)
  --n_processes N_PROCESSES
                        Number of processes (for parallel integrators) (default: None)
  --n_samples N_SAMPLES
                        Number of samples (for MC-based integrators) (default: None)
  --seed SEED           seed (for randomized integrators) (default: None)
```
