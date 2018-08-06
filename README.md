# wmi-pa
~~Python 2~~ Python 3 implementation of the method presented in:

  [Efficient WMI via SMT-Based Predicate Abstraction](https://www.ijcai.org/proceedings/2017/100)  
  Paolo Morettin, Andrea Passerini, Roberto Sebastiani,
  in Proceedings of IJCAI 2017
  
  (the latest python 2 release can be found in Releases > last_py2_version)

## Required software:
- [sympy](http://www.sympy.org/en/index.html)
- [NetworkX](https://networkx.github.io/)
- [Matplotlib](https://matplotlib.org/)
- [Latte Integrale](https://www.math.ucdavis.edu/~latte/)
- [pysmt and MathSAT5](https://github.com/pysmt/pysmt)

LattE's binary folder must be present in the PATH environment variable.

In order to run the comparison with [PRAiSE](http://aic-sri-international.github.io/aic-praise/), the command line interface .jar
must be called *praise.jar* and must be located in *src/thirdparties/*.

The version used in the experiments reported in the paper is provided.



## Examples
We provide some examples that show how to write a model and evaluate weighted model integrals on it.
To run the code in *examples/*, type: python exampleX.py

## Experiments
The *experiments/* folder contains the code used to run the experiments reported in the paper.
Each experiment folder comes with Shell scripts that show how to run them.

A sample dataset for the Strategic Road Network is provided in
*experiments/srn/data/*. It needs to be uncompressed before running the experiment.
