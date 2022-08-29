from setuptools import setup, find_packages

setup(
    name="youte",
    author="Digital Observatory",
    authhor_email="digitalobservatory@qut.edu.au",
    version="0.0.1b",
    description="Command-line tool to collect video metadata and comments from Youtube API",
    long_description="file: README.md",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Pyhon :: 3.8'
        ],
    packages=find_packages(where="src"),
    install_requires=[
        'click >= 8.0.3',
        'requests >= 2.27.1',
        'tqdm >= 4.64.0',
        'python-dateutil >= 2.8.2',
        'configobj >= 5.0.6'
        ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'youte=youte.__main__:youte'
            ]
        }
)
