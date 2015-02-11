import os
from setuptools import setup, find_packages
from gittkt.GitTktDefines import GITTKT_VERSION

setup(
    url = "",
    author = "Thurston Stone",
    author_email = "tstone2077@gmail.com",
    name = 'git-tkt',
    version = GITTKT_VERSION,
    description = "Distributed bug tracking for Git.",
    test_suite = "gittkt.tests",
    keywords = "bug, tracking, git, distributed",
    packages = find_packages(exclude=["t_*"]),
    install_requires = ['gitshelve>=0.1.1'],
    tests_require = ['gitshelve>=0.1.1'],
    classifiers = [
        "Topic :: Software Development :: Bug Tracking",
        "Development Status :: 2 - Pre-Alpha",
        ],
    entry_points = {
        'console_scripts': ['git-tkt = gittkt.gittktCLI:EntryPoint']
        },
    data_files = [
        ('git-tkt',['LICENSE','LICENSE.gitshelve','README'])
        ],
    )

