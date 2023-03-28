#!/usr/bin/env python3
import os
import subprocess
from setuptools import setup, find_packages


__dir__ = os.path.dirname(__file__)
version = subprocess.check_output(
    [
        "python3",
        f"{os.path.abspath(os.path.dirname(__file__))}/openlane/__version__.py",
    ],
    encoding="utf8",
)

requirements = open("requirements.txt").read().strip().split("\n")
setup(
    name="openlane",
    packages=find_packages(),
    package_data={
        "openlane": [
            "py.typed",
            "open_pdks_rev",
            "scripts/*",
            "scripts/**/*",
            "scripts/**/**/*",
            "smoke_test_design/*",
            "smoke_test_design/**/*",
        ]
    },
    version=version,
    description="An infrastructure for implementing chip design flows",
    long_description=open("Readme.md").read(),
    long_description_content_type="text/markdown",
    author="Efabless Corporation and Contributors",
    author_email="donn@efabless.com",
    install_requires=requirements,
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
    ],
    entry_points={"console_scripts": ["openlane = openlane.__main__:cli"]},
    python_requires=">3.8",
)
