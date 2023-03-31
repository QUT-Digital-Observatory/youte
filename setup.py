import pathlib

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()

__version__ = "2.0.2"

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

if __name__ == "__main__":
    setup(
        name="youte",
        author="Digital Observatory",
        authhor_email="digitalobservatory@qut.edu.au",
        version=__version__,
        description="Command-line tool to collect video metadata and comments from "
        "Youtube API",
        long_description=long_description,
        long_description_content_type="text/markdown",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python :: 3.8",
        ],
        packages=find_packages(where="src"),
        install_requires=[
            "click >= 8.0.3",
            "requests >= 2.27.1",
            "python-dateutil >= 2.8.2",
            "configobj >= 5.0.6",
            "typing_extensions >= 4.5.0",
        ],
        python_requires=">=3.8",
        entry_points={"console_scripts": ["youte=youte.cli:youte"]},
    )
