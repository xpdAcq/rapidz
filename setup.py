#!/usr/bin/env python

from os.path import exists
from setuptools import setup

packages = ["rapidz", "rapidz.dataframe"]

tests = [p + ".tests" for p in packages]


setup(
    name="rapidz",
    version='0.2.1',
    description="Streams",
    url="http://github.com/xpdAcq/rapidz/",
    maintainer="Simon Billinge",
    maintainer_email="simon.billinge@gmail.com",
    license="BSD",
    keywords="streams",
    packages=packages + tests,
    python_requires='>=3.9',
    long_description=(
        open("README.rst").read() if exists("README.rst") else ""
    ),
    install_requires=list(open("requirements.txt").read().strip().split("\n")),
    zip_safe=False,
)
