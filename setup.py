from setuptools import setup

setup(
    name='slcli',
    version='0.0.1',
    packages=['slcli'],
    entry_points={
        'console_scripts': [
            'slcli = slcli.main:main',
        ],
    },
)
