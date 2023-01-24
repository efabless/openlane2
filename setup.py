#!/usr/bin/env python3
import glob
from setuptools import setup, find_packages

from openlane import __version__

requirements = open("requirements.txt").read().strip().split("\n")
setup(
    name="openlane",
    packages=find_packages(),
    package_data={
        "openlane": [
            "py.typed",
        ]
        + glob.glob("./scripts/**/*")
    },
    version=__version__,
    description="A full open source RTL to GDSII flow",
    long_description=open("Readme.md").read(),
    long_description_content_type="text/markdown",
    author="Efabless Corporation and Contributors",
    author_email="donn@efabless.com",
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
    ],
    entry_points={"console_scripts": ["openlane = openlane.__main__:cli"]},
    python_requires=">3.8",
)
