# SA-WMI-PA-SK

[![Build Status](https://travis-ci.org/unitn-sml/wmi-pa.svg?branch=master)](https://travis-ci.org/unitn-sml/wmi-pa)

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

[SMT-based Weighted Model Integration with Structure Awareness and Multiple Integration Approaches](https://arxiv.org/abs/2302.06188)  
Giuseppe Spallitta, Gabriele Masina, Paolo Morettin, Andrea Passerini, Roberto Sebastiani

## pywmi

WMI-PA is now part of [pywmi](https://github.com/weighted-model-integration/pywmi/), a general framework for Weighted
Model Integration that offers a number of different solvers, a command-line interface, etc.

## Installation

Base version:

```bash
pip install wmipa
```

Version with support for NRA:

```bash
pip install "wmipa[nra]"
```

### Additional requirements

To install all the requirements, run the following command:

```bash
wmipa-install --all
```

and then add the following lines to the `~/.bashrc` file:

```
PATH=$HOME/.wmipa/latte/bin:$PATH
PATH=$HOME/.wmipa/approximate-integration/bin:$PATH
```

#### Separate installation

If you want to install the requirements separately, you can use the following commands.

At least one following integration backend is needed:

* [LattE integrale](https://www.math.ucdavis.edu/~latte/) - Exact integration (recommended):
  ```bash
  wmipa-install --latte
  ```
  Add `$HOME/latte/bin` to the PATH environment variable by adding the following line to the `~/.bashrc` file:
  ```
  PATH=$HOME/.wmipa/latte/bin:$PATH
  ```

* [VolEsti](https://github.com/masinag/approximate-integration) - Approximated integration:
  ```bash
  wmipa-install --volesti
  ```
  Add `bin` to the PATH environment variable by adding the following line to the `~/.bashrc` file:
  ```
  PATH=$HOME/.wmipa/approximate-integration/bin:$PATH
  ```

[MathSAT5](http://mathsat.fbk.eu/)

```bash
pysmt-install --msat
```

For the SA-WMI-PA-SK mode, a slightly customized version of MathSAT5 is needed.

```bash
wmipa-install --msat-custom
```

This script substitutes the files
`<venv>/lib/python3.8/site-packages/_mathsat.cpython-38-x86_64-linux-gnu.so` and
`<venv>/lib/python3.8/site-packages/mathsat.py`
with those provided in the `bin/` folder of this repository
(Python3.8 under Linux x86_64 is required).

Support for other OS and Python versions will be added in the near future.

## Examples

We provide some examples that show how to write a model and evaluate weighted model integrals on it.
To run the code in *examples/*, type:

    python exampleX.py
