# wmi-pa
[![Build Status](https://travis-ci.org/unitn-sml/wmi-pa.svg?branch=master)](https://travis-ci.org/unitn-sml/wmi-pa)

Python 3 implementation of the method presented in:

  [Efficient WMI via SMT-Based Predicate Abstraction](https://www.ijcai.org/proceedings/2017/100)  
  Paolo Morettin, Andrea Passerini, Roberto Sebastiani,
  in Proceedings of IJCAI 2017

## Installation

    pip install wmipa

The algorithm additionally requires:
- [LattE integrale](https://www.math.ucdavis.edu/~latte/) LattE's binary folder must be present in the PATH environment variable.
- [MathSAT5](http://mathsat.fbk.eu/) Run:
    pysmt-install --msat

## Examples
We provide some examples that show how to write a model and evaluate weighted model integrals on it.
To run the code in *examples/*, type: python exampleX.py

## pywmi

We suggest to check out [pywmi](https://github.com/weighted-model-integration/pywmi/), a general framework for Weighted Model Integration that supports WMI-PA and other solving techniques.
