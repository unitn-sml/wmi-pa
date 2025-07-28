import os
from os import path

from setuptools import find_packages, setup

NAME = "wmipa"
DESCRIPTION = "Weighted Model Integration PA (Predicate Abstraction) solver."
URL = "http://github.com/unitn-sml/wmi-pa"
EMAIL = "paolo.morettin@unitn.it"
AUTHOR = "Gabriele Masina, Paolo Morettin, Giuseppe Spallitta"
REQUIRES_PYTHON = ">=3.9.0"
VERSION = "0.1.8"

# What packages are required for this module to be executed?
REQUIRED = [
    "networkx",
    "numpy",
    "PySMT>=0.9.7.dev333",
    "scipy",
]

# What packages are optional?
EXTRAS = {
    'test': ["pytest", "pytest-runner"],
    'nra': ["pysmt @ git+https://git@github.com/masinag/pysmt@nrat#egg=pysmt"],
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
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    python_requires=REQUIRES_PYTHON,
    packages=find_packages(exclude=("test", "examples")),
    zip_safe=False,
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    cmdclass={
        #        'upload': UploadCommand,
        #        'install': PostInstallCommand,
    },
    entry_points={
        "console_scripts": [
            "wmipa-install = wmipa_cli.install:run",
        ]
    },
)
