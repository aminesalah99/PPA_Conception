"""
Setup script for the Dental Design Application
"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the requirements file
with open("src/requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="dental-design-app",
    version="2.0.0",
    author="Dental Design Team",
    author_email="contact@dental-design.com",
    description="A professional dental arch design application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ppa_conception",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        "": ["*.png", "*.jpg", "*.jpeg", "*.json"],
    },
    entry_points={
        "console_scripts": [
            "dental-design-app=main:main",
        ],
    },
)
