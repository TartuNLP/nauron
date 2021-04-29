import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

version = {}
with open("nauron/__version__.py") as fp:
    exec(fp.read(), version)

setuptools.setup(
    name="nauron",
    version=version['__version__'],
    author="University of Tartu",
    author_email="ping@tartunlp.ai",
    description="A Python library for creating distributed and scalable web services.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TartuNLP/nauron",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Framework :: Flask"
    ],
    license='GPLv3',
    install_requires=[
        'pika>=1.1.0',
        'flask>=1.1.2',
        'flask-cors>=3.0.9',
        'dataclasses>=0.7; python_version < "3.7.0"'
    ]
)
