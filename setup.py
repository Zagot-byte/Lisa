from setuptools import setup, find_packages

setup(
    name="lisa",
    version="0.1.0",
    py_modules=["cli", "spawner"],   # top-level .py files (not in a package dir)
    packages=find_packages(),        # core/, model/, memory/, tools/, utils/, env/
    entry_points={
        "console_scripts": [
            "lisa=cli:main",
        ],
    },
    python_requires=">=3.10",
)
