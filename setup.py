#!/usr/bin/env python3
import os
import subprocess
from setuptools import setup, find_packages

module_name = "openlane"

__dir__ = os.path.abspath(os.path.dirname(__file__))
version = subprocess.check_output(
    [
        "python3",
        os.path.join(
            __dir__,
            module_name,
            "__version__.py",
        ),
    ],
    encoding="utf8",
)

requirements = open("requirements.txt").read().strip().split("\n")
setup(
    name=module_name,
    packages=find_packages(),
    package_data={
        module_name: [
            "py.typed",
            "open_pdks_rev",
            "scripts/*",
            "scripts/**/*",
            "scripts/**/**/*",
            "examples/*",
            "examples/**/*",
            "examples/**/**/*",
        ]
    },
    version=version,
    description="An infrastructure for implementing chip design flows",
    long_description=open(os.path.join(__dir__, "Readme.md")).read(),
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
    entry_points={
        "console_scripts": [
            "openlane = openlane.__main__:cli",
            "openlane.steps = openlane.steps.__main__:cli",
            "openlane.config = openlane.config.__main__:cli",
            "openlane.state = openlane.state.__main__:cli",
            "openlane.env_info = openlane:env_info_cli",
        ]
    },
    python_requires=">3.8",
)
