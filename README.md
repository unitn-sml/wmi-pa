# wmi-pa
[![Build Status](https://travis-ci.org/unitn-sml/wmi-pa.svg?branch=master)](https://travis-ci.org/unitn-sml/wmi-pa)

Python 3 implementation of the method presented in:

  [Efficient WMI via SMT-Based Predicate Abstraction](https://www.ijcai.org/proceedings/2017/100)  
  Paolo Morettin, Andrea Passerini, Roberto Sebastiani,
  in Proceedings of IJCAI 2017

## pywmi

WMI-PA is now part of [pywmi](https://github.com/weighted-model-integration/pywmi/), a general framework for Weighted Model Integration that offers a number of different solvers, a command-line interface, etc.

## Installation

    pip install wmipa

### Additional requirements

[LattE integrale](https://www.math.ucdavis.edu/~latte/) 
LattE's binary folder must be present in the PATH environment variable.

[MathSAT5](http://mathsat.fbk.eu/)
Run:

    pysmt-install --msat

## Examples
We provide some examples that show how to write a model and evaluate weighted model integrals on it.
To run the code in *examples/*, type: python exampleX.py
