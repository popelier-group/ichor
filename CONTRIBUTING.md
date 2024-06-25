# How to contribute to ichor

# Installation instructions

Install the development version of the packages which will install all extra packages needed to build documentation and run unit tests.

```
pip install -e ichor_core[dev]
pip install -e ichor_hpc
pip install -e ichor_cli
```
## Set up pre-commit

[Pre-commit](https://pre-commit.com/) is used to run hooks such as [black](https://github.com/psf/black) for formatting and others. Run

```
pre-commit install
```

to download and set up pre-commit hooks.

To run all hooks on all Python files in the repository, do:

```
git ls-files -- '*.py' | xargs pre-commit run --files
```

# Unit Testing

Currently only `ichor.core` has unit tests because this is the only part of the code that can be tested in an easy way.

```
pytest ichor_core/tests
```

will run all the tests in the repository. Similarly, you can run specific unit tests by giving the exact path to the directory/file containing the unit tests you want to run.

# Documentation

[Sphinx](https://www.sphinx-doc.org/en/master/) is used to build the documentation from the source code. The documentation is found in the `docs/source` directory. Additional example `.rst` files are also found there which are incorporated in the final html documentation. Examples notebooks and other `.rst` pages which are not automatically created by `sphinx-apidoc` to be displayed in the final documentation must be written manually.


To build the documentation locally, run

```
cd docs
make docs
```

which will generate the html files. Opening the `index.html` file into a browser will show the documentation.

# Making pull requests

Pull requests are very welcome! Please ensure you follow the above steps as when a pull request is created, the same hooks are ran with Github Actions which check if the code is formatted correctly, as well as if the unit tests and documentation building are completed successfully.

# Discussions and Issues

If you have questions on `ichor` or would like to discuss new features please open up a discussion page. Any requests or issues with the code can be opened up as issues.
