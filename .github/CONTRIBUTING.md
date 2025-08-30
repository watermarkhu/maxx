# Contributing

In order to contribute to the current repository, make sure to have gone through the following steps. 

## Environment

After cloning your fork, setup the environment with [uv](https://docs.astral.sh/uv/), and install the pre-commit hooks. 

```bash
uv sync
uv run pre-commit install
```
## Testing

To run the tests in the repository, first initialize the *submodules*:

```bash
git submodule init
git submodule update
```

and then run with `uv`:

```bash
uv run pytest
```

### MATLAB regression test

We have setup a regression test that compares the path resolution by the package and by MATLAB. This test is written as a [MATLAB test](../tests/TestMatlabPath.m), which uses [pyenv](https://www.mathworks.com/help/matlab/ref/pyenv.html) to load the python environment and call the package directly. 

This test is run in CI but is not executed with `uv run pytest`. If you wish to run the test locally, you'll need to run the [test](../tests/TestMatlabPath.m) in MATLAB.

```matlab
runtests('./tests');
```

## Commits 

The [pre-commit](https://pre-commit.com/) hooks will make sure that before every commit, the following checks are done:

1. Checking `pyproject.toml` validity
2. Checking local `uv.lock` file
3. `uv check` and `uv format`
4. `ty check` type-checking

Commits should follow the [Conventional Commits](https://www.conventionalcommits.org) specification. Based on your commits (and the pull request title), the version bump will be automatically determined.  

## Pull requests

Pull request should be targetting `main` directly. If commits in the pull request did not follow [Conventional Commits](https://www.conventionalcommits.org), make sure that the pull request title does. 
