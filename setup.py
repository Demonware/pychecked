"""pychecked's setup.py."""


import io
import re

from setuptools import setup
from setuptools.command.test import test as TestCommand


def find_version(filename):
    """Uses re to pull out the assigned value to __version__ in filename."""

    with io.open(filename, encoding="utf-8") as version_file:
        version_match = re.search(r'__version__ = [\'"]([^\'"]*)[\'"]',
                                  version_file.read(), re.M)
    if version_match:
        return version_match.group(1).strip()
    return "0.0-version-unknown"


class PyTest(TestCommand):
    def finalize_options(self):
        """Stolen from http://pytest.org/latest/goodpractises.html."""

        TestCommand.finalize_options(self)
        self.test_suite = True
        self.test_args = [
            "-v",
            "-rx",
            "--cov-report", "term-missing",
            "--cov", find_packages(exclude=("test*", "bin", "example*"))[0],
            "--junitxml=test-results.xml",
        ]

    def run_tests(self):
        """Also shamelessly stolen."""

        # have to import here, outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


setup(
    name="pychecked",
    version=find_version("pychecked/__init__.py"),
    author="Adam Talsma",
    author_email="adam@demonware.net",
    packages=["pychecked"],
    cmdclass={"test": PyTest},
    tests_require=["pytest", "pytest-cov"],
    url="https://github.com/Demonware/pychecked",
    description="Python3+ type checking for annotated function signatures.",
    long_description="Python type checking for annotated function signatures.",
    download_url="https://github.com/Demonware/pychecked",
    license="BSD",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
    ],
)
