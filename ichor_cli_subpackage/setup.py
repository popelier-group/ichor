from setuptools import setup, find_namespace_packages

setup(
    name='ichor_cli',
    packages=find_namespace_packages(include=['ichor*'])
)