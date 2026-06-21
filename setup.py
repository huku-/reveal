#!/usr/bin/env python

import setuptools

scripts = []

packages = [
    "reveal",
    "reveal.algorithms",
    "reveal.data",
    "reveal.datasets",
    "reveal.features",
    "reveal.graphs",
    "reveal.matchers",
]

package_data = {
    "reveal": ["py.typed"],
    "reveal.data": ["logging.ini", "logging-debug.ini", "vex_insn_cls.json"],
}

entry_points = {"console_scripts": ["reveal = reveal.__main__:main"]}

requirements = open("requirements.txt").read().splitlines()

setuptools.setup(
    name="REveal",
    version="1.0",
    description="REveal",
    author="Chariton Karamitas",
    author_email="huku@census-labs.com",
    url="https://github.com/huku-/reveal",
    scripts=scripts,
    packages=packages,
    package_dir={"": "src"},
    package_data=package_data,
    entry_points=entry_points,
    install_requires=requirements,
    zip_safe=False,
)
