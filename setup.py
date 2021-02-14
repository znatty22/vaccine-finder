from os import path

from setuptools import find_packages, setup

# requirements from requirements.txt
root_dir = path.dirname(path.abspath(__file__))
with open(path.join(root_dir, "requirements.txt"), "r") as f:
    requirements = f.read().splitlines()

setup(
    name="vaccine-finder",
    description="Find stores with open vaccine appointments",
    url="https://github.com/znatty22/vaccine-finder",
    packages=find_packages(),
    python_requires=">=3.6, <4",
    install_requires=requirements,
)
