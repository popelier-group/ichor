from setuptools import setup, find_namespace_packages

setup(
    name='ichor-hpc',
    author="Matthew Burn, Yulian Manchev",
    author_email="matthew.burn@postgrad.manchester.ac.uk, yulian.manchev@postgrad.manchester.ac.uk",
    project_urls = {"github": "https://github.com/popelier-group/ICHOR"},
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
    description="ICHOR hpc subpackage.",
    packages=find_namespace_packages(include=['ichor*']),
    python_requires=">=3.7",
    install_requires=["pandas"]
)