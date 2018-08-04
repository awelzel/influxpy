#!/usr/bin/env python
from setuptools import setup, find_packages

setup(

    name="influxpy",
    version="0.0.1",
    description="Python logging handler that sends messages to InfluxDB using the line protocol.",
    keywords="logging influxdb udp tcp",
    author="Arne Welzel",
    author_email="arne.welzel@gmail.com",
    url="https://github.com/awelzel/influxpy",
    license="BSD License",
    packages=find_packages(),
    classifiers=["License :: OSI Approved :: BSD License",
                 "Programming Language :: Python :: 2",
                 "Programming Language :: Python :: 3"],
)
