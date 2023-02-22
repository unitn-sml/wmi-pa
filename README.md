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

  [SMT-based Weighted Model Integration with Structure Awareness and Multiple Integration Approaches](TODO)  
  Giuseppe Spallitta, Gabriele Masina, Paolo Morettin, Andrea Passerini, Roberto Sebastiani

## pywmi

WMI-PA is now part of [pywmi](https://github.com/weighted-model-integration/pywmi/), a general framework for Weighted Model Integration that offers a number of different solvers, a command-line interface, etc.

## Installation
Base version:

    pip install wmipa

Version with support for NRA:

    pip install "wmipa[nra]"
### Additional requirements

At least one following integration backend is needed:
  * [LattE integrale](https://www.math.ucdavis.edu/~latte/) - Exact integration (recommended):
    ```[bash]
    sudo apt install -y libntl-dev libcdd-dev libcdd-tools
    wget https://github.com/latte-int/latte/releases/download/version_1_7_6/latte-int-1.7.6.tar.gz
    tar -xzf latte-int-1.7.6.tar.gz
    cd latte-int-1.7.6
    ./configure GXX="g++ -std=c++11" CXX="g++ -std=c++11" --prefix=$HOME/latte && make && make install
    cd ..
    ```
    Add `$HOME/latte/bin` to the PATH environment variable:
    ```[bash]
    export PATH=$HOME/latte/bin:$PATH
    ```

  * [VolEsti](https://github.com/masinag/approximate-integration) - Approximated integration:
    ```[bash] 
    ```[bash]
    git clone https://github.com/masinag/approximate-integration
    cd approximate-integration
    make
    ```
    Add `bin` to the PATH environment variable:
    ```[bash]
    export PATH=$PWD/bin:$PATH
    ```

[MathSAT5](http://mathsat.fbk.eu/)
```[bash]
pysmt-install --msat
```
For the SA-WMI-PA-SK mode, a slightly customized version of MathSAT5 is needed.
In order to install it, you need to substitute the file 
`<venv>/lib/python3.8/site-packages/_mathsat.cpython-38-x86_64-linux-gnu.so`
with the one provided in the `bin/` folder of this repository 
(Python3.8 under Linux x86_64 is required).

Support for other OS and Python versions will be added in the near future.

## Examples
We provide some examples that show how to write a model and evaluate weighted model integrals on it.
To run the code in *examples/*, type: python exampleX.py
