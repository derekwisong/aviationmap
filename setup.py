import os
from setuptools import setup

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as handle:
        return handle.read().strip()

setup(
        name="avwx_map",
        version=read('ledmap/VERSION'),
        author="Derek Wisong",
        author_email="derek@wisong.net",
        description="An aviation weather map",
        long_description=read('README.md'),
        license="GPL",
        keywords=["aviation", "weather", "map", "led", "vfr", "metar"],
        packages=['avwx', 'ledmap'],
        entry_points={'console_scripts':['ledmap=ledmap.map:main']},
        package_data={'ledmap': ["config.yml"]},
        install_requires=['wheel',
                          'rpi.gpio',
                          'adafruit-ws2801',
                          'requests',
                          'pyyaml']
)
