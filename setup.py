import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="wavepl",
    version="0.0.1",
    description="Library for processing WAV files.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Krishna-Sivakumar/wapl",
    author="Krishna Sivakumar",
    author_email="krishnasivaprogrammer@gmail.com",
    packages=["wapl"],
    include_package_data=True,
    install_requires=["numpy"],
)

