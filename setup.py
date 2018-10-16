import os
from setuptools import setup, find_packages


VERSION = "0.1"

src_dir = os.path.dirname(__file__)

install_requires = [
    "requests",
    "iso8601",
]

tests_require = [
    "flake8",
    "mypy",
    "pytest"
]


setup(
    name="instaclustr-cli",
    version=VERSION,
    author="Daniel Miranda",
    author_email="danielkza2@gmail.com",
    license="MIT License",
    url="https://github.com/Cobliteam/instaclustr-cli",
    description="Instaclustr Command Line",
    long_description=open("README.md").read(),
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'testing': tests_require},  # for tox
    entry_points={
        'console_scripts': [
            'instaclustr-cli = instaclustr.cli:main'
        ]
    }
)
