import nox


@nox.session
def lint(session):
    session.install("flake8", "black")
    session.run("flake8", "src/youte/")
    session.run("black", "--check", "src/youte/")
