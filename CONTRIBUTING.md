# Contributing Guide

Thanks for your interest in contributing to this project! This document aims to
serve as a friendly guide for making your first contribution.

## Developing

You will need:

- Python >= 3.8
- Virtual environment

### Cloning the project

```sh
git clone git@github.com:izavits/entrant.git
cd entrant
```

### Installing npm dependencies

Install the dependencies by running:

```sh
pip install -r requirements.txt
```

### Testing & linting

To run the test suite, run the following command:

```sh
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv
pytest
```

## Sending a pull request

When sending a pull request, consider the following guidelines:

- Write a concise commit message explaining your changes.

- If applies, write more descriptive information in the commit body.

- Refer to the issue/s your pull request fixes (if there are issues in the github repo).

- Write a descriptive pull request title.

- Squash commits when possible.

Before your pull request can be merged, the following conditions must hold:

- All tests pass.

- The coding style aligns with the project's convention.

- Your changes are confirmed to be working.


**Working on your first Pull Request?** See here: [Contributing to a Project on GitHub](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project)
