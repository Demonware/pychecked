"""pychecked's setup.py."""


import importlib
from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand


pychecked = importlib.import_module("pychecked")
type_checking = importlib.import_module("pychecked.type_checking")


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
    version=pychecked.__version__,
    author="Adam Talsma",
    author_email="adam@demonware.net",
    packages=find_packages(exclude="test"),
    cmdclass={"test": PyTest},
    tests_require=["pytest", "pytest-cov"],
    url="https://github.com/Demonware/pychecked",
    description="Python3+ type checking for annotated function signatures",
    long_description=type_checking.__doc__,
    download_url="https://github.com/Demonware/pychecked",
    license="BSD",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
    ],
)
