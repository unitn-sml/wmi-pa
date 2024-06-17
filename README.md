# WMI-PA

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

[Enhancing SMT-based Weighted Model Integration by structure awareness](https://www.sciencedirect.com/science/article/pii/S0004370224000031)  
Giuseppe Spallitta, Gabriele Masina, Paolo Morettin, Andrea Passerini, Roberto Sebastiani,  
in Artificial Intelligence, Volume 328, 2024

## Installation

Base version:

```bash
pip install wmipa
```

### Additional requirements

The base version of the solver requires at least one integration backend to be installed.

Additional dependencies are needed to also support NRA theory.

We provide a script that automatically installs all the requirements. The script has only been tested on Ubuntu
distributions.

#### All-in-one installation

To install all the mandatory and optional requirements, run

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

* [PyXadd](https://github.com/weighted-model-integration/pywmi) - Symbolic integration:
  ```bash
  wmipa-install --symbolic
  ```

The [MathSAT5](http://mathsat.fbk.eu/) SMT solver is required

```bash
wmipa-install --msat
```

To support NRA theory (PI, Sin, Exp,
ecc.), [a customized version of PySMT](https://github.com/masinag/pysmt/tree/nrat) must be installed via

```bash
wmipa-install --nra
```

## Examples

We provide some examples that show how to write a model and evaluate weighted model integrals on it.
To run the code in *examples/*, type:

    python exampleX.py
