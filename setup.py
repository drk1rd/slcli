import setuptools

setuptools.setup(
    name="slcli",
    version="0.0.1",
    description="A simple CLI for SimpleLogin",
    author="drk1rd",
    url="https://github.com/drk1rd/slcli",
    packages=["slcli"],
    scripts=["bin/slcli"],
    install_requires=["simplelogin"],
)
