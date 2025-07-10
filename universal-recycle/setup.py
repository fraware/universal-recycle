from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("recycle/requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="universal-recycle",
    version="0.1.0",
    author="Universal Recycle Team",
    description="A polyglot, manifest-driven build system for recycling and modernizing code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/universal-recycle",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "recycle=recycle.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml"],
    },
    keywords="build-system, polyglot, code-recycling, bazel, python, cpp",
    project_urls={
        "Bug Reports": "https://github.com/your-org/universal-recycle/issues",
        "Source": "https://github.com/your-org/universal-recycle",
        "Documentation": "https://github.com/your-org/universal-recycle#readme",
    },
)
