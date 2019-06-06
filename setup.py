"""Foamgen package"""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="foamgen",
    version="0.1.0",
    author="Pavel Ferkl",
    author_email="pavel.ferkl@gmail.com",
    description="Generate virtual closed-cell or open-cell foam structure.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/japaf/foamgen",
    packages=setuptools.find_packages(),
    classifiers=[
        "Intended Audience :: Science/Research",
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: C++",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
)
