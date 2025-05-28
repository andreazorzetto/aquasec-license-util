from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aquasec-license-utility",
    version="0.2.0",
    author="Andrea Zorzetto",
    author_email="your-email@example.com",
    description="CLI tool for Aqua Security license utilization analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/andreazorzetto/aquasec-license-utility",
    py_modules=["aqua_license_util"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "aquasec>=0.1.0",
        "prettytable>=3.5.0",
        "cryptography>=41.0.0",
    ],
    entry_points={
        "console_scripts": [
            "aquasec-license=aqua_license_util:main",
        ],
    },
)