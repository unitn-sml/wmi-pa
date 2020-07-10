import os
import shutil
import sys

from setuptools import setup, find_packages, Command
from setuptools.command.install import install
from os import path

NAME = 'wmipa'
DESCRIPTION = 'Weighted Model Integration PA (Predicate Abstraction) solver.'
URL = 'http://github.com/unitn-sml/wmi-pa'
EMAIL = 'paolo.morettin@unitn.it'
AUTHOR = 'Paolo Morettin'
REQUIRES_PYTHON = '>=3.5.0'
VERSION = "0.1.5"

# What packages are required for this module to be executed?
REQUIRED = [
    'pysmt', 'numpy', 'sympy', 'networkx'
]

# What packages are optional?
EXTRAS = {
#        'sdd': ["pysdd"]
}

here = os.path.abspath(os.path.dirname(__file__))

with open(path.join(here, "README.md")) as ref:
    long_description = ref.read()

"""
class PostInstallCommand(install):
    def run(self):
        install.run(self)
        os.system("pysmt-install --msat --confirm-agreement") # additionally install mathsat
"""

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    author=AUTHOR,
    author_email=EMAIL,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    python_requires=REQUIRES_PYTHON,
    packages=find_packages(exclude=('test', 'examples')),
    zip_safe=False,
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    setup_requires=['pytest-runner'],
    tests_require=["pytest"],
    cmdclass={
#        'upload': UploadCommand,
#        'install': PostInstallCommand,
    },
)
