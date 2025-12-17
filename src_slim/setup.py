# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:36:23 2025

@author: msi
"""

from setuptools import setup, find_packages

setup(
    name="blending-optimizer",
    version="1.0.0",
    author="Équipe Projet RO INSA",
    author_email="equipe@insa.tn",
    description="Application d'optimisation de formulation alimentaire avec PL/PLM",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/votre-equipe/blending-optimization",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "gurobipy>=10.0.0",
        "PyQt5>=5.15.0",
        "matplotlib>=3.5.0",
        "numpy>=1.21.0",
        "pandas>=1.3.0",
    ],
    include_package_data=True,
    package_data={
        "": ["data/*.json"],
    },
    entry_points={
        "console_scripts": [
            "blending-optimizer=main:main",
        ],
    },
)