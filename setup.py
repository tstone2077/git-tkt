import os
from setuptools import setup, find_packages
from gittkt.gittkt import GIT_TKT_VERSION

setup(
    url = "",
    author = "Thurston Stone",
    author_email = "tstone2077@gmail.com",
    name = 'git-tkt',
    version = GIT_TKT_VERSION,
    description = "Distributed bug tracking for Git.",
    keywords = "bug, tracking, git, distributed",
    packages = find_packages(exclude=["t_*"]),
    classifiers = [
        "Topic :: Software Development :: Bug Tracking",
        "Development Status :: 2 - Pre-Alpha",
        ],
    entry_points = {
        'console_scripts': ['git-tkt = gittkt.gittkt:main']
        },
#    data_files = [
#        ('git-tkt',['LICENSE','README'])
#        ],
    )

