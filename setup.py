"""
Setup script for Burpy
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="burpy",
    version="1.0.0",
    author="Burpy Team",
    author_email="burpy@example.com",
    description="A CLI-based web security testing tool similar to Burp Suite",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/burpy",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "burpy=burpy.cli.main:cli",
        ],
    },
    keywords="security, web, testing, proxy, vulnerability, scanner, fuzzing",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/burpy/issues",
        "Source": "https://github.com/yourusername/burpy",
    },
)