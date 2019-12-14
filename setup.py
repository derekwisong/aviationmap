import os
from setuptools import setup

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as handle:
        return handle.read()

setup(
        name="avwx_map",
        version="0.0.1",
        author="Derek Wisong",
        author_email="derek@wisong.net",
        description="An aviation weather map",
        long_description=read('README.md'),
        license="GPL",
        keywords="aviation weather map led vfr metar",
        packages=['avwx', 'ledvfrmap']
)
