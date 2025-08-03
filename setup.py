"""Setup script for sqlfluff-templater-schemachange."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sqlfluff-templater-schemachange",
    version="0.1.0",
    author="Thomas MacKay",
    author_email="mackay.thomas@gmail.com",
    description="A standalone SQLFluff templater providing schemachange-compatible Jinja templating without schemachange dependency",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MACKAT05/sqlfluff-templater-schemachange",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Database",
    ],
    python_requires=">=3.8",
    install_requires=[
        "sqlfluff>=2.0.0",
        "PyYAML>=5.1",
    ],
    entry_points={
        "sqlfluff": [
            "sqlfluff_templater_schemachange = sqlfluff_templater_schemachange",
        ],
    },
    keywords="sqlfluff templater schemachange snowflake database linting",
    project_urls={
        "Bug Reports": "https://github.com/MACKAT05/sqlfluff-templater-schemachange/issues",
        "Source": "https://github.com/MACKAT05/sqlfluff-templater-schemachange",
    },
)