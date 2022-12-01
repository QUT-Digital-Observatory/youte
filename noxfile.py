import nox

nox.options.sessions = ["lint"]


@nox.session
def lint(session):
    session.install("flake8", "black")
    session.run("flake8", "src/youte/")
    session.run("black", "--check", "src/youte/")


@nox.session(python=["3.8", "3.9", "3.10"])
def test(session):
    session.run("pip", "install", "--upgrade", "pip", "setuptools", "wheel")
    session.install(".")
    session.install("pytest")
    session.run("pytest", "tests")
