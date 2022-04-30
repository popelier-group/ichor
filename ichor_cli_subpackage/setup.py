from setuptools import setup, find_namespace_packages

setup(
    name='ichor_cli',
    version="3.0.0",
    description="ICHOR library subpackage.",
    packages=find_namespace_packages(include=['ichor*']),
    install_requires=["ichor_lib"]
)