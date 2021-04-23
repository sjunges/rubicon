import os
from setuptools import setup

# Get the long description from the README file
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md')) as f:
    long_description = f.read()

setup(
    name="rubicon",
    version="0.1",
    author="S. Junges",
    author_email="sebastian.junges@berkeley.edu",
    url="https://github.com/moves-rwth/storm-project-starter-python",
    description="Model checking with probabilistic inference via Stormpy and Dice.",
    long_description=long_description,
    long_description_content_type='text/markdown',

    packages=["rubicon"],
    install_requires=[
        "stormpy>=1.3.0", "click", "numpy"
    ],
    python_requires='>=3',
)
